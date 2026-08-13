"""Built-in playbooks + a library (Phase 08 — docs/13-Agents/Playbooks.md §4).

The shipped **triage → enrich → corroborate → ticket** playbook is a supervised investigation:
read-only steps run automatically, and the consequential ``create_ticket`` step is an **approval
checkpoint** (the runtime pauses the run until a human approves). It is bound to the Phase 06
``investigation-assistant`` agent, inheriting its least-privilege scope — it can *not* isolate a
host. New playbooks register in a `PlaybookLibrary`; each is validated against its base agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dula_agents.agents import build_investigation_agent, get_agent
from dula_agents.runtime import AgentDefinition

from dula_automation.playbook import (
    Condition,
    Playbook,
    PlaybookError,
    PlaybookStep,
    Ref,
    Template,
    validate_playbook,
)

INVESTIGATION_AGENT = "investigation-assistant"


def _triage_enrich_ticket() -> Playbook:
    top_indicator = Ref(step="triage", path="alerts.0.indicator", default="")
    top_host = Ref(step="triage", path="alerts.0.host", default="")
    top_title = Ref(step="triage", path="alerts.0.title", default="suspicious activity")
    return Playbook(
        name="triage-enrich-ticket",
        title="Triage, enrich, and open a ticket",
        description=(
            "Review open alerts, enrich the top indicator, corroborate against logs, and — with "
            "human approval — open an incident ticket."
        ),
        base_agent=INVESTIGATION_AGENT,
        tags=("investigation", "uc-03", "uc-15"),
        steps=(
            PlaybookStep(
                id="triage",
                tool="list_alerts",
                description="Review the tenant's open alerts to anchor the investigation.",
                args={"limit": 5},
            ),
            PlaybookStep(
                id="enrich",
                tool="enrich_indicator",
                description="Enrich the top alert's indicator (IOCs + ATT&CK techniques).",
                when=Condition.ref_nonempty(top_indicator),
                bind={"value": top_indicator},
            ),
            PlaybookStep(
                id="corroborate",
                tool="search_logs",
                description="Corroborate by searching logs for the affected host/indicator.",
                when=Condition.step_ok("triage"),
                args={"limit": 10},
                bind={"query": Ref(step="triage", path="alerts.0.host", default="")},
            ),
            PlaybookStep(
                id="ticket",
                tool="create_ticket",
                description="Open an incident ticket (consequential — requires human approval).",
                when=Condition.step_ok("triage"),
                bind={
                    "title": Template("Investigation: {title}", {"title": top_title}),
                    "body": Template(
                        "Automated triage of {title}. Indicator: {indicator}; host: {host}.",
                        {"title": top_title, "indicator": top_indicator, "host": top_host},
                    ),
                },
            ),
        ),
    )


@dataclass
class PlaybookLibrary:
    """Name → Playbook, validated against its base agent on registration."""

    _playbooks: dict[str, Playbook] = field(default_factory=dict)

    def register(self, playbook: Playbook, base_agent: AgentDefinition) -> None:
        validate_playbook(playbook, base_agent)
        self._playbooks[playbook.name] = playbook

    def get(self, name: str) -> Playbook | None:
        return self._playbooks.get(name)

    def names(self) -> list[str]:
        return sorted(self._playbooks)

    def all(self) -> list[Playbook]:
        return [self._playbooks[n] for n in self.names()]


def default_library() -> PlaybookLibrary:
    """The built-in library. Each playbook is validated against its resolved base agent."""
    library = PlaybookLibrary()
    investigation = build_investigation_agent()
    library.register(_triage_enrich_ticket(), investigation)
    return library


def resolve_base_agent(playbook: Playbook) -> AgentDefinition:
    """Resolve the agent a playbook is bound to (its scope/limits source)."""
    agent = get_agent(playbook.base_agent)
    if agent is None:  # pragma: no cover - built-ins reference known agents
        raise PlaybookError(f"playbook '{playbook.name}' references unknown agent")
    return agent
