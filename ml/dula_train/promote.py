"""CLI to promote or roll back a registered Dula AI version through the lifecycle
stages (docs/09-MLOps/ModelLifecycle.md).

Thin argparse wrapper around dula_ml.lifecycle.promote -- the same "logic lives in the
torch-free, CI-tested dula-ml package" split as decide.py, so the transition rules
cannot drift from what CI tests. A rollback is just `--to-stage production` pointed at
a version that is currently `superseded`.
"""

from __future__ import annotations

import argparse
import json

from dula_ml.lifecycle import STAGES, promote


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Promote (or roll back) a registered candidate to a new lifecycle stage."
    )
    parser.add_argument("--manifest", default="out/registry.jsonl")
    parser.add_argument("--version", required=True)
    parser.add_argument("--to-stage", required=True, choices=sorted(s.value for s in STAGES))
    parser.add_argument("--actor", default=None, help="who/what triggered this promotion")
    parser.add_argument("--note", default="", help="free-text reason, e.g. an incident summary")
    args = parser.parse_args()

    entry = promote(args.manifest, args.version, args.to_stage, actor=args.actor, note=args.note)
    print(json.dumps({"version": entry.version, "stage": entry.stage, "notes": entry.notes}))


if __name__ == "__main__":
    main()
