"""Tests for RunConfig and output path layout."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pytest

from mudidi.config.output_paths import resolve_output_layout
from mudidi.config.run_config import RunConfig, stage_from_cli


def test_stage_from_cli_all() -> None:
    assert stage_from_cli("all") == "both"


def test_inference_run_config_defaults(tmp_path: Path) -> None:
    pages = tmp_path / "pages"
    pages.mkdir()
    out = tmp_path / "out"
    config = RunConfig(
        benchmark=False,
        pages_dir=pages,
        output_dir=out,
        stage="all",
    )
    assert config.prompt_mode == "inference"
    assert config.stage1_source == "predictions"
    layout = resolve_output_layout(config)
    assert layout.stage1_root == out / "stage-1"
    assert layout.stage2_root == out / "stage-2"
    assert layout.field_cheatsheet_path == out / "field_cheatsheet.json"


def test_benchmark_run_config_layout(tmp_path: Path) -> None:
    pages = tmp_path / "pages"
    pages.mkdir()
    out = tmp_path / "outputs"
    config = RunConfig(
        benchmark=True,
        pages_dir=pages,
        output_dir=out,
        experiment_name="exp1",
        stage="1",
        stage1_source="gold",
    )
    assert config.prompt_mode == "benchmark"
    layout = resolve_output_layout(config)
    assert layout.stage1_root == out / "stage-1" / "exp1"
    assert layout.inference is False


def test_run_config_from_namespace(tmp_path: Path) -> None:
    pages = tmp_path / "snippets"
    pages.mkdir()
    out = tmp_path / "out"
    args = Namespace(
        benchmark=False,
        pages=str(pages),
        input_image=str(pages),
        output_dir=str(out),
        output=str(out),
        stage="all",
        stage1_source=None,
        experiment_name="default",
        stage2_experiment_name=None,
        stage1_output_subdir="stage-1",
        samples_dir=None,
        languages=None,
        intro=None,
        alphabet=None,
        ocr_text=None,
        cheatsheet_page=None,
    )
    config = RunConfig.from_namespace(args)
    assert config.prompt_mode == "inference"
    assert config.internal_stage == "both"
