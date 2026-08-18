"""CLI: scheduled production health check + auto-rollback trigger
(docs/09-MLOps/ModelLifecycle.md #3). Intended to run on a schedule
(deploy/argo/dula-ai-monitor-cronworkflow.yaml).

Thin argparse wrapper around dula_ml.monitor.check_production_health -- same
logic-in-dula-ml/thin-CLI split as decide.py and promote.py, so the drift-detection rule
cannot drift from what CI tests. Exits non-zero on a detected regression so the scheduler
step itself shows failed, which is a real, monitorable signal even without a live
Prometheus/metrics exporter (docs/16-Operations/Observability.md notes that exporter as
FUTURE).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dula_ml.evaluation import EvalReport
from dula_ml.monitor import check_production_health


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compare a freshly computed evaluation against the current production "
            "version's recorded baseline; roll back to the previous version on regression."
        )
    )
    parser.add_argument("--manifest", default="out/registry.jsonl")
    parser.add_argument(
        "--live-report",
        required=True,
        help="EvalReport JSON freshly computed for whatever is currently in production",
    )
    parser.add_argument("--quality-tolerance", type=float, default=0.0)
    parser.add_argument("--safety-tolerance", type=float, default=0.0)
    parser.add_argument("--actor", default="scheduled-monitor")
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    live_report = EvalReport.model_validate_json(Path(args.live_report).read_text(encoding="utf-8"))
    result = check_production_health(
        args.manifest,
        live_report,
        quality_tolerance=args.quality_tolerance,
        safety_tolerance=args.safety_tolerance,
        actor=args.actor,
        note=args.note,
    )
    print(
        json.dumps(
            {
                "checked_version": result.checked_version,
                "regressed": result.regressed,
                "reasons": result.gate.reasons,
                "rolled_back_to": result.rolled_back_to,
            }
        )
    )
    if result.regressed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
