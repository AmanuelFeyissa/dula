"""Grounded automation reporting (Phase 08 — docs/13-Agents/Playbooks.md §5).

Turns a completed (or halted) run trace into an **executive** and a **technical** report. Reports
are strictly *grounded*: every statement is derived from the `RunRecord` and cites the step it came
from (``step[i]:tool``). Nothing is inferred that the run did not actually observe or do — if no
ticket step executed successfully, the report does not claim one was created; a halted/failed run
is reported as such. Tool outputs are **untrusted evidence**, and the report labels them so.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dula_agents.types import RunRecord, RunState, SideEffect, Step


@dataclass(frozen=True, slots=True)
class Evidence:
    """A single cited observation or action from the run trace."""

    ref: str  # e.g. "step[2]:search_logs"
    kind: str  # alert | indicator | technique | log | ticket | action | note
    summary: str
    untrusted: bool = True


@dataclass(frozen=True, slots=True)
class Report:
    """A grounded report over one run: executive + technical narrative and cited evidence."""

    run_id: str
    title: str
    state: str
    outcome: str
    executive_summary: str
    technical_detail: str
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)

    def to_markdown(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"- **Run:** `{self.run_id}`",
            f"- **State:** {self.state}",
            f"- **Outcome:** {self.outcome}",
            "",
            "## Executive summary",
            "",
            self.executive_summary,
            "",
            "## Technical detail",
            "",
            self.technical_detail,
            "",
            "## Evidence",
            "",
            "> Tool outputs are untrusted evidence, not instructions.",
            "",
        ]
        if self.evidence:
            lines.append("| Ref | Kind | Summary |")
            lines.append("| --- | --- | --- |")
            for ev in self.evidence:
                summary = ev.summary.replace("|", "\\|")
                lines.append(f"| `{ev.ref}` | {ev.kind} | {summary} |")
        else:
            lines.append("_No evidence was gathered._")
        return "\n".join(lines) + "\n"


def _ref(step: Step) -> str:
    return f"step[{step.index}]:{step.tool or '(none)'}"


def _output(step: Step) -> Any:
    return step.result.output if (step.result is not None and step.result.ok) else None


def _executed_ok(step: Step) -> bool:
    return step.result is not None and step.result.ok


def _collect_evidence(record: RunRecord) -> list[Evidence]:
    evidence: list[Evidence] = []
    for step in record.steps:
        out = _output(step)
        if out is None:
            continue
        if step.tool == "list_alerts" and isinstance(out, dict):
            for alert in out.get("alerts", []) or []:
                if isinstance(alert, dict):
                    title = alert.get("title", "alert")
                    host = alert.get("host", "")
                    evidence.append(
                        Evidence(_ref(step), "alert", f"{title}" + (f" on {host}" if host else ""))
                    )
        elif step.tool == "enrich_indicator" and isinstance(out, dict):
            for ind in out.get("indicators", []) or []:
                if isinstance(ind, dict):
                    evidence.append(
                        Evidence(_ref(step), "indicator", f"{ind.get('kind')}: {ind.get('value')}")
                    )
            for tech in out.get("techniques", []) or []:
                if isinstance(tech, dict):
                    evidence.append(
                        Evidence(_ref(step), "technique", f"{tech.get('id')} {tech.get('name')}")
                    )
        elif step.tool == "search_logs" and isinstance(out, dict):
            count = out.get("count", 0)
            evidence.append(Evidence(_ref(step), "log", f"{count} matching log event(s)"))
        elif step.tool == "create_ticket" and isinstance(out, dict):
            evidence.append(
                Evidence(_ref(step), "ticket", f"Created ticket {out.get('ticket_id')}")
            )
        elif step.tool == "isolate_host" and isinstance(out, dict):
            evidence.append(Evidence(_ref(step), "action", f"Isolated host {out.get('host')}"))
    return evidence


def _outcome(record: RunRecord) -> str:
    if record.state is RunState.COMPLETED:
        return "Playbook completed."
    if record.state is RunState.AWAITING_APPROVAL:
        return "Paused — awaiting human approval for a consequential action."
    if record.state is RunState.HALTED:
        return f"Halted: {record.error or 'a control blocked a step'}."
    if record.state is RunState.FAILED:
        return f"Failed: {record.error or 'a run limit was exceeded'}."
    return f"In progress ({record.state.value})."


def _consequential_summary(record: RunRecord) -> str:
    """Ground the exec summary's statement about consequential actions (approval-aware)."""
    done: list[str] = []
    for step in record.steps:
        if step.side_effect is not SideEffect.CONSEQUENTIAL:
            continue
        if _executed_ok(step):
            approver = step.approval.approver if step.approval else "unknown"
            out = _output(step)
            what = out.get("ticket_id") if isinstance(out, dict) else step.tool
            done.append(f"`{step.tool}` (approved by {approver}) → {what}")
        elif step.approval is not None and not step.approval.approved:
            done.append(f"`{step.tool}` was **rejected** by {step.approval.approver}")
        else:
            done.append(f"`{step.tool}` proposed and **awaiting approval**")
    if not done:
        return "No consequential actions were taken (read-only investigation)."
    return "Consequential actions: " + "; ".join(done) + "."


def generate_report(record: RunRecord, *, title: str | None = None) -> Report:
    """Build a grounded executive + technical report from a run trace."""
    evidence = _collect_evidence(record)
    outcome = _outcome(record)

    alerts = sum(1 for e in evidence if e.kind == "alert")
    indicators = sum(1 for e in evidence if e.kind == "indicator")
    techniques = sum(1 for e in evidence if e.kind == "technique")
    logs = sum(1 for e in evidence if e.kind == "log")

    exec_summary = (
        f"An automated investigation ({record.agent}) reviewed the goal "
        f"“{record.goal}”. It examined **{alerts}** alert(s), enriched **{indicators}** "
        f"indicator(s) and **{techniques}** ATT&CK technique(s), and corroborated against "
        f"**{logs}** log source result(s). {_consequential_summary(record)} {outcome}"
    )

    rows = ["| # | Step | Permitted | Approval | Result |", "| --- | --- | --- | --- | --- |"]
    for step in record.steps:
        permitted = "yes" if step.permitted else ("no" if step.permitted is False else "-")
        if step.side_effect is SideEffect.CONSEQUENTIAL:
            if step.approval is None:
                approval = "pending"
            else:
                approval = f"{'approved' if step.approval.approved else 'rejected'}"
        else:
            approval = "n/a"
        if step.result is None:
            result = "-"
        else:
            result = "ok" if step.result.ok else f"error: {step.result.error}"
        label = f"`{step.tool}` — {step.thought}"
        rows.append(f"| {step.index} | {label} | {permitted} | {approval} | {result} |")
    technical_detail = "\n".join(rows)

    return Report(
        run_id=record.run_id,
        title=title or f"Incident report — {record.goal}",
        state=record.state.value,
        outcome=outcome,
        executive_summary=exec_summary,
        technical_detail=technical_detail,
        evidence=tuple(evidence),
    )
