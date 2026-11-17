"""Run the synthetic private-training example and export its audit log."""

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "dp-llm-training"))
sys.path.insert(0, str(_REPO_ROOT))

import private_training  # noqa: E402

from tools.provenance import build_provenance  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Train on synthetic data and save privacy accounting with provenance."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--audit-log", type=Path, default=Path("artifacts/private-training-audit.json")
    )
    args = parser.parse_args(argv)
    if not private_training.TORCH_AVAILABLE or not private_training.OPACUS_AVAILABLE:
        print("Install private-training dependencies: pip install -e .[dp]", file=sys.stderr)
        return 1
    report = private_training.run_private_demo(args.seed)
    for name in ("steps", "stopped_reason", "final_epsilon", "sample_rate"):
        print(f"{name}: {getattr(report, name)}")
    payload = report.to_audit_log(
        build_provenance(
            "measured",
            "dp-llm-training/examples/private_training_demo.py",
            seed=args.seed,
        )
    )
    args.audit_log.parent.mkdir(parents=True, exist_ok=True)
    args.audit_log.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
