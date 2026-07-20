"""Command-line entry point for DEMO evaluation, keys, and receipt verification."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .demo import run_demo_case
from .demo_keys import (
    DEMO_KEYRING_PATH,
    DEMO_PRIVATE_KEY_PATH,
    PUBLIC_SAMPLE_KEYRING_PATH,
    DemoKeyBootstrapError,
    bootstrap_demo_keypair,
)
from .offline_receipts import (
    LOCAL_SAMPLE_MATERIALS_PATH,
    LOCAL_SAMPLE_RECEIPT_PATH,
    PUBLIC_SAMPLE_MATERIALS_PATH,
    PUBLIC_SAMPLE_RECEIPT_PATH,
    OfflineReceiptError,
    issue_sample_receipt_files,
    verify_receipt_files,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aelitium-decision")
    subcommands = parser.add_subparsers(dest="command", required=True)

    demo = subcommands.add_parser("demo", help="run pre-computed golden cases")
    demo.add_argument("case", choices=["T1", "T2", "T3", "all"])
    demo.add_argument("--compact", action="store_true", help="emit compact JSON")

    keys = subcommands.add_parser("keys", help="manage local DEMO signing material")
    key_commands = keys.add_subparsers(dest="key_command", required=True)
    bootstrap = key_commands.add_parser(
        "bootstrap", help="create or validate the ignored local DEMO keypair"
    )
    bootstrap.add_argument("--private-key", type=Path, default=DEMO_PRIVATE_KEY_PATH)
    bootstrap.add_argument("--keyring", type=Path, default=DEMO_KEYRING_PATH)

    sample = subcommands.add_parser("sample", help="issue a local sample receipt")
    sample_commands = sample.add_subparsers(dest="sample_command", required=True)
    issue = sample_commands.add_parser(
        "issue", help="issue the fixed scenario with local signing material"
    )
    issue.add_argument("--private-key", type=Path, default=DEMO_PRIVATE_KEY_PATH)
    issue.add_argument("--keyring", type=Path, default=DEMO_KEYRING_PATH)
    issue.add_argument(
        "--receipt-output", type=Path, default=LOCAL_SAMPLE_RECEIPT_PATH
    )
    issue.add_argument(
        "--materials-output", type=Path, default=LOCAL_SAMPLE_MATERIALS_PATH
    )

    receipt = subcommands.add_parser("receipt", help="offline receipt operations")
    receipt_commands = receipt.add_subparsers(dest="receipt_command", required=True)
    verify = receipt_commands.add_parser(
        "verify", help="verify a receipt using external public inputs only"
    )
    verify.add_argument("--receipt", type=Path, default=PUBLIC_SAMPLE_RECEIPT_PATH)
    verify.add_argument("--materials", type=Path, default=PUBLIC_SAMPLE_MATERIALS_PATH)
    verify.add_argument("--keyring", type=Path, default=PUBLIC_SAMPLE_KEYRING_PATH)
    return parser


def _emit(payload: object, *, compact: bool = False, error: bool = False) -> None:
    destination = sys.stderr if error else sys.stdout
    if compact:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")), file=destination)
    else:
        print(json.dumps(payload, indent=2, sort_keys=True), file=destination)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        case_names = ["T1", "T2", "T3"] if args.case == "all" else [args.case]
        results = [run_demo_case(case_name) for case_name in case_names]
        payload = results if args.case == "all" else results[0]
        _emit(payload, compact=args.compact)
        return 0

    if args.command == "keys" and args.key_command == "bootstrap":
        try:
            result = bootstrap_demo_keypair(
                private_key_path=args.private_key, keyring_path=args.keyring
            )
        except DemoKeyBootstrapError as exc:
            _emit({"status": "ERROR", "reason": exc.code}, error=True)
            return 2
        _emit(result.as_dict())
        return 0

    if args.command == "sample" and args.sample_command == "issue":
        try:
            result = issue_sample_receipt_files(
                private_key_path=args.private_key,
                keyring_path=args.keyring,
                receipt_path=args.receipt_output,
                materials_path=args.materials_output,
            )
        except OfflineReceiptError as exc:
            _emit({"status": "ERROR", "reason": exc.code}, error=True)
            return 2
        _emit(result.as_dict())
        return 0

    if args.command == "receipt" and args.receipt_command == "verify":
        try:
            result = verify_receipt_files(
                receipt_path=args.receipt,
                materials_path=args.materials,
                keyring_path=args.keyring,
            )
        except OfflineReceiptError as exc:
            _emit({"status": "ERROR", "reason": exc.code}, error=True)
            return 2
        _emit(result.as_dict())
        return 0 if result.valid else 1

    raise AssertionError("unhandled command")


if __name__ == "__main__":
    raise SystemExit(main())
