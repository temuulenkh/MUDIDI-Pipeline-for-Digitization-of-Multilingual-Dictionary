"""MUDIDI command-line entry point."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    """Dispatch ``mudidi`` subcommands."""
    parser = argparse.ArgumentParser(
        prog="mudidi",
        description="Dictionary OCR and MDF extraction (inference and benchmark modes).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Run Stage 1 / Stage 2 extraction on dictionary pages.",
    )
    from mudidi.cli.run import register_run_arguments, run_from_args

    register_run_arguments(run_parser)

    eval_parser = subparsers.add_parser("eval", help="Evaluation utilities.")
    eval_sub = eval_parser.add_subparsers(dest="eval_command", required=True)

    eval_stage1 = eval_sub.add_parser("stage1", help="Stage 1 flat evaluation.")
    eval_stage1.set_defaults(_handler=_eval_stage1)

    eval_stage2 = eval_sub.add_parser("stage2", help="Stage 2 MDF evaluation.")
    eval_stage2.set_defaults(_handler=_eval_stage2)

    args, remaining = parser.parse_known_args(argv)
    if args.command == "run":
        from mudidi.cli.run import run_from_args

        return run_from_args(args, remaining)
    if args.command == "eval":
        return args._handler(remaining)
    return 1


def _eval_stage1(remaining: list[str]) -> int:
    from mudidi.cli.evaluate_stage1 import main as eval_main

    old_argv = sys.argv
    try:
        sys.argv = ["mudidi-eval-flat", *remaining]
        eval_main()
        return 0
    finally:
        sys.argv = old_argv


def _eval_stage2(remaining: list[str]) -> int:
    from mudidi.cli.evaluate_stage2_mdf import main as eval_main

    old_argv = sys.argv
    try:
        sys.argv = ["mudidi-eval-stage2-mdf", *remaining]
        eval_main()
        return 0
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    raise SystemExit(main())
