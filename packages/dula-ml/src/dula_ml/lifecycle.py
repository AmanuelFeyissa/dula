"""Model registry lifecycle stage transitions (docs/09-MLOps/ModelLifecycle.md).

A shipped candidate moves Register(None) -> Staging -> Canary -> Production, can be
Superseded when a newer version takes over, and a Superseded version can be re-promoted
straight back to Production -- that re-promotion *is* a rollback
(docs/09-MLOps/DeploymentPipelines.md #2: "rollback = re-point the production stage tag").
Rejected candidates (a canary that regressed) can only be archived.

Every transition is a *new* entry appended to the same JSONL manifest the ship/retire
decision already lives in (dula_ml.registry) -- past entries are never mutated, so the
manifest stays a complete, auditable history. Promoting to `production` additionally
supersedes whichever version currently holds it (see `promote`'s docstring) -- that cascade
is not expressible in `_LEGAL_TRANSITIONS` below, since it mutates a *second* entry rather
than the one being promoted.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import os
import time
from pathlib import Path

from dula_ml.registry import RegistryEntry, Stage, append_entry, load_manifest

STAGES: frozenset[Stage] = frozenset(Stage)

# Legal (from_stage -> {to_stage, ...}) edges. `None` = freshly registered candidate.
_LEGAL_TRANSITIONS: dict[Stage | None, frozenset[Stage]] = {
    None: frozenset({Stage.STAGING}),
    Stage.STAGING: frozenset({Stage.CANARY}),
    Stage.CANARY: frozenset({Stage.PRODUCTION, Stage.REJECTED}),
    Stage.PRODUCTION: frozenset({Stage.SUPERSEDED}),
    Stage.SUPERSEDED: frozenset({Stage.PRODUCTION, Stage.ARCHIVED}),
    Stage.REJECTED: frozenset({Stage.ARCHIVED}),
}


@contextlib.contextmanager
def _manifest_lock(manifest_path: str | Path, timeout: float = 10.0):  # type: ignore[no-untyped-def]
    """Serialize concurrent `promote()` calls against the same manifest.

    A promotion to `production` is two sequential appends (supersede the old one, then
    register the new one) -- without this, two processes promoting different versions to
    `production` at nearly the same time could both compute the same "current production"
    snapshot and both append, leaving two versions marked `production`. A plain lock file
    (atomic create, not a real distributed lock) is enough for the single-host/single-repo
    scale this manifest is designed for.
    """
    lock_path = Path(f"{manifest_path}.lock")
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise TimeoutError(f"timed out waiting for lock on {manifest_path}") from None
            time.sleep(0.05)
    try:
        yield
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.remove(lock_path)


def _latest_by_version(entries: list[RegistryEntry]) -> dict[str, RegistryEntry]:
    latest: dict[str, RegistryEntry] = {}
    for entry in entries:
        latest[entry.version] = entry
    return latest


def _current_production_from_latest(latest: dict[str, RegistryEntry]) -> RegistryEntry | None:
    for entry in latest.values():
        if entry.stage == Stage.PRODUCTION:
            return entry
    return None


def current_production(manifest_path: str | Path) -> RegistryEntry | None:
    """The entry currently staged `production`, or None if nothing has been promoted."""
    return _current_production_from_latest(_latest_by_version(load_manifest(manifest_path)))


def _transition_note(
    from_stage: Stage | None, to_stage: Stage, actor: str | None, note: str
) -> str:
    parts = [f"{from_stage.value if from_stage else 'candidate'} -> {to_stage.value}"]
    if actor:
        parts.append(f"(by {actor})")
    if note:
        parts.append(f": {note}")
    return " ".join(parts)


def promote(
    manifest_path: str | Path,
    version: str,
    to_stage: str | Stage,
    *,
    actor: str | None = None,
    note: str = "",
) -> RegistryEntry:
    """Transition `version` to `to_stage`, appending a new manifest entry.

    Raises ValueError if `version` is unknown, was retired, or the transition isn't a
    legal edge on the lifecycle state diagram. Promoting a *different* version to
    `production` automatically supersedes whatever version currently holds that stage,
    so at most one version is ever `production` at a time.
    """
    to_stage = Stage(to_stage)
    with _manifest_lock(manifest_path):
        entries = load_manifest(manifest_path)
        latest = _latest_by_version(entries)
        current = latest.get(version)
        if current is None:
            raise ValueError(f"no registry entry for version {version!r}")
        if current.stage is None and current.decision != "ship":
            raise ValueError(f"version {version!r} was retired and cannot be promoted")

        legal = _LEGAL_TRANSITIONS.get(current.stage, frozenset())
        if to_stage not in legal:
            legal_names = sorted(s.value for s in legal)
            raise ValueError(
                f"illegal transition {current.stage!r} -> {to_stage.value!r} for version "
                f"{version!r} (legal targets from {current.stage!r}: {legal_names or 'none'})"
            )

        if to_stage == Stage.PRODUCTION:
            existing_prod = _current_production_from_latest(latest)
            if existing_prod is not None and existing_prod.version != version:
                _append_transition(
                    manifest_path,
                    existing_prod,
                    Stage.SUPERSEDED,
                    actor=actor,
                    note=f"superseded by {version}",
                )

        return _append_transition(manifest_path, current, to_stage, actor=actor, note=note)


def _append_transition(
    manifest_path: str | Path,
    entry: RegistryEntry,
    to_stage: Stage,
    *,
    actor: str | None,
    note: str,
) -> RegistryEntry:
    new_entry = entry.model_copy(
        update={
            "stage": to_stage,
            "created_at": dt.datetime.now(dt.UTC).isoformat(),
            "notes": _transition_note(entry.stage, to_stage, actor, note),
        }
    )
    append_entry(new_entry, manifest_path)
    return new_entry
