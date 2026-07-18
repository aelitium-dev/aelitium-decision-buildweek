"""Command-line entry point for deterministic D1 demo evaluations."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from .demo import run_demo_case


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aelitium-decision")
    subcommands = parser.add_subparsers(dest="command", required=True)

    demo = subcommands.add_parser("demo", help="run pre-computed golden cases")
    demo.add_argument("case", choices=["T1", "T2", "T3", "all"])
    demo.add_argument("--compact", action="store_true", help="emit compact JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    case_names = ["T1", "T2", "T3"] if args.case == "all" else [args.case]
    results = [run_demo_case(case_name) for case_name in case_names]
    payload = results if args.case == "all" else results[0]
    if args.compact:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
