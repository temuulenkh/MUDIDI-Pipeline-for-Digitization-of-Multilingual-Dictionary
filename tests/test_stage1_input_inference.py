"""Tests for stage-1 transcript resolution in inference layout."""

from __future__ import annotations

from pathlib import Path

from mudidi.utils.stage1_input import resolve_stage1_transcript_for_stage2, stage1_flat_path


def test_inference_layout_predictions_path(tmp_path: Path) -> None:
    stem = "page_1"
    page_dir = tmp_path / "stage-1" / stem
    page_dir.mkdir(parents=True)
    flat = stage1_flat_path(page_dir, stem)
    flat.write_text("line one\n", encoding="utf-8")

    resolved = resolve_stage1_transcript_for_stage2(
        tmp_path,
        stem,
        "flat",
        source="predictions",
        inference_layout=True,
    )
    assert resolved == flat
