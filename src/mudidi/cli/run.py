"""``mudidi run`` command — inference and benchmark extraction."""

from __future__ import annotations

import argparse
from typing import Sequence

from mudidi.config.run_config import RunConfig, stage_from_cli
from mudidi.llm.prompt_store import configure_prompts, default_prompts_path


def register_run_arguments(parser: argparse.ArgumentParser) -> None:
    """Register arguments for ``mudidi run``."""
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--benchmark",
        action="store_true",
        help="Benchmark mode: samples tree layout, gold defaults, no neighbor context.",
    )

    parser.add_argument(
        "--pages",
        dest="pages",
        help="Directory of dictionary page snippets (pdf/png/jpg/jpeg). "
        "Alias for --input-image.",
    )
    parser.add_argument(
        "--input-image",
        dest="input_image",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        help="Output directory. Inference: stage-1/ and stage-2/ subdirs. "
        "Alias for --output.",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--samples-dir",
        dest="samples_dir",
        help="Benchmark: parent directory of per-language sample folders.",
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        default=None,
        help="Benchmark: subset of language folders under --samples-dir.",
    )
    parser.add_argument(
        "--intro",
        help="Path to dictionary introduction (directory of images/PDFs).",
    )
    parser.add_argument(
        "--alphabet",
        help="Path to alphabet list (.txt or markdown) or alphabet image.",
    )
    parser.add_argument(
        "--ocr-text",
        dest="ocr_text",
        help="Directory of OCR hint files keyed by page stem.",
    )
    parser.add_argument(
        "--stage",
        choices=["1", "2", "all"],
        default="all",
        help="Run Stage 1 only, Stage 2 only, or both (default: all).",
    )
    parser.add_argument(
        "--stage1-source",
        choices=["gold", "predictions"],
        default=None,
        dest="stage1_source",
        help="Stage 2 transcript source. Benchmark default: gold. Inference: predictions.",
    )
    parser.add_argument(
        "--cheatsheet-page",
        dest="cheatsheet_page",
        help="Page stem for Pass 1 field discovery (default: first page).",
    )
    parser.add_argument(
        "--prompts-file",
        type=str,
        default=None,
        dest="prompts_file",
        help="Path to PROMPT.json (default: bundled assets).",
    )


def _merge_extract_args(_run_args: argparse.Namespace, remaining: Sequence[str]) -> list[str]:
    """Forward unhandled flags to the legacy extract driver."""
    return list(remaining)


def run_from_args(run_args: argparse.Namespace, remaining: Sequence[str]) -> int:
    """Execute ``mudidi run`` by delegating to the extract driver."""
    pages = run_args.pages or run_args.input_image
    output = run_args.output_dir or run_args.output

    if run_args.benchmark:
        if not run_args.samples_dir and not pages:
            raise SystemExit("--benchmark requires --samples-dir or --pages with sample layout.")
    elif not pages or not output:
        raise SystemExit("Inference mode requires --pages and --output-dir.")

    if run_args.prompts_file:
        configure_prompts(run_args.prompts_file)
    else:
        configure_prompts(default_prompts_path())

    import sys

    from mudidi.cli import extract as extract_module

    argv = ["mudidi-run"]
    if run_args.benchmark:
        argv.append("--benchmark")
    if pages:
        argv.extend(["--pages", pages, "--input-image", pages])
    if output:
        argv.extend(["--output-dir", output, "--output", output])
    if run_args.samples_dir:
        argv.extend(["--samples-dir", run_args.samples_dir])
    if run_args.languages:
        argv.extend(["--languages", *run_args.languages])
    if run_args.intro:
        argv.extend(["--intro", run_args.intro])
    if run_args.alphabet:
        argv.extend(["--alphabet", run_args.alphabet])
    if run_args.ocr_text:
        argv.extend(["--ocr-text", run_args.ocr_text])
    internal_stage = stage_from_cli(run_args.stage)
    argv.extend(["--stage", internal_stage])
    if run_args.stage1_source:
        argv.extend(["--stage1-source", run_args.stage1_source])
    if run_args.cheatsheet_page:
        argv.extend(["--cheatsheet-page", run_args.cheatsheet_page])
    if run_args.prompts_file:
        argv.extend(["--prompts-file", run_args.prompts_file])
    argv.extend(_merge_extract_args(run_args, remaining))

    old_argv = sys.argv
    try:
        sys.argv = argv
        return extract_module.main()
    finally:
        sys.argv = old_argv
