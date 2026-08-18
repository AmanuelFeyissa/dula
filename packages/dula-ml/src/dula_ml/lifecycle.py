"""Model registry lifecycle stage transitions (docs/09-MLOps/ModelLifecycle.md).

A shipped candidate moves Register(None) -> Staging -> Canary -> Production, can be
Superseded when a newer version takes over, and a Superseded version can be re-promoted
straight back to Production -- that re-promotion *is* a rollback
(docs/09-MLOps/DeploymentPipelines.md #2: "rollback = re-point the production stage tag").
Rejected candidates (a canary that regressed) can only be archived.

Every transition is a *new* entry appended to the same JSONL manifest the ship/retire
decision already lives in (dula_ml.registry) -- past entries are never mutated, so the
manifest stays a complete, auditable history.
"""

from __future__ import annotations

import datetime as dt

from dula_ml.registry import RegistryEntry, append_entry, load_manifest

STAGES: frozenset[str] = frozenset(
    {"staging", "canary", "production", "rejected", "superseded", "archived"}
)

# Legal (from_stage -> {to_stage, ...}) edges. `None` = freshly registered candidate.
_LEGAL_TRANSITIONS: dict[str | None, frozenset[str]] = {
    None: frozenset({"staging"}),
    "staging": frozenset({"canary"}),
    "canary": frozenset({"production", "rejected"}),
    "production": frozenset({"superseded"}),
    "superseded": frozenset({"production", "archived"}),
    "rejected": frozenset({"archived"}),
}


def _latest_by_version(entries: list[RegistryEntry]) -> dict[str, RegistryEntry]:
    latest: dict[str, RegistryEntry] = {}
    for entry in entries:
        latest[entry.version] = entry
    return latest


def _current_production_from_latest(latest: dict[str, RegistryEntry]) -> RegistryEntry | None:
    for entry in latest.values():
        if entry.stage == "production":
            return entry
    return None


def current_production(manifest_path: str) -> RegistryEntry | None:
    """The entry currently staged `production`, or None if nothing has been promoted."""
    return _current_production_from_latest(_latest_by_version(load_manifest(manifest_path)))


def _transition_note(from_stage: str | None, to_stage: str, actor: str | None, note: str) -> str:
    parts = [f"{from_stage or 'candidate'} -> {to_stage}"]
    if actor:
        parts.append(f"(by {actor})")
    if note:
        parts.append(f": {note}")
    return " ".join(parts)


def promote(
    manifest_path: str,
    version: str,
    to_stage: str,
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
    entries = load_manifest(manifest_path)
    latest = _latest_by_version(entries)
    current = latest.get(version)
    if current is None:
        raise ValueError(f"no registry entry for version {version!r}")
    if current.stage is None and current.decision != "ship":
        raise ValueError(f"version {version!r} was retired and cannot be promoted")

    legal = _LEGAL_TRANSITIONS.get(current.stage, frozenset())
    if to_stage not in legal:
        raise ValueError(
            f"illegal transition {current.stage!r} -> {to_stage!r} for version {version!r} "
            f"(legal targets from {current.stage!r}: {sorted(legal) or 'none'})"
        )

    if to_stage == "production":
        existing_prod = _current_production_from_latest(latest)
        if existing_prod is not None and existing_prod.version != version:
            _append_transition(
                manifest_path,
                existing_prod,
                "superseded",
                actor=actor,
                note=f"superseded by {version}",
            )

    return _append_transition(manifest_path, current, to_stage, actor=actor, note=note)


def _append_transition(
    manifest_path: str,
    entry: RegistryEntry,
    to_stage: str,
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
