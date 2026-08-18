"""Model card + eval report rendering (docs/09-MLOps/ModelRegistry.md).

Every registered candidate ships with a model card that states its base model, data, metrics,
the ship/retire decision, intended use, and safety posture — required before promotion.
"""

from __future__ import annotations

from dula_ml.registry import RegistryEntry


def render_model_card(entry: RegistryEntry) -> str:
    c, b = entry.candidate_eval, entry.baseline_eval
    lines = [
        f"# Model Card — {entry.artifact_name()}",
        "",
        f"- **Base model:** {entry.base_model}",
        f"- **Method:** {entry.method.upper()}",
        f"- **Dataset version:** {entry.dataset_version}",
        f"- **Decision:** **{entry.decision.upper()}**",
        f"- **Created:** {entry.created_at}",
        f"- **Weight SHA-256:** {entry.weight_sha256 or 'n/a'}",
        "",
        "## Evaluation (candidate vs baseline)",
        "",
        "| Metric | Candidate | Baseline |",
        "|--------|-----------|----------|",
        f"| Benchmark accuracy | {c.accuracy:.3f} | {b.accuracy:.3f} |",
        f"| Safety refusal rate | {c.safety_refusal_rate:.3f} | {b.safety_refusal_rate:.3f} |",
        f"| Benchmark items | {c.n_items} | {b.n_items} |",
        f"| Safety items | {c.n_safety} | {b.n_safety} |",
        "",
        "## Gate",
        "",
        *[f"- {reason}" for reason in entry.gate.reasons],
        "",
        "## Intended use & safety",
        "",
        "- Defensive cybersecurity assistance only; refuses operational offensive requests.",
        "- Served behind the Dula LLM Gateway (guardrails, tenant isolation, audit).",
        "- All facts should be grounded via RAG; the model is not a source of truth for CVEs.",
    ]
    if entry.decision == "retire":
        lines += [
            "",
            "## Retirement note",
            "",
            "This candidate did **not** beat the general-model baseline without regressing "
            "safety, so it is **retired** (not shipped). The platform continues on the general "
            "model with RAG. Retiring a non-improving candidate is a valid, expected outcome — "
            "shipping a worse or less-safe model is never acceptable.",
        ]
    return "\n".join(lines) + "\n"
