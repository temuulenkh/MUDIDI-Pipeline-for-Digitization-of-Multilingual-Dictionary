"""Tests for mudidi CLI argument wiring."""

from __future__ import annotations

from pathlib import Path

import pytest

from mudidi.cli.main import main


def test_mudidi_run_help() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["run", "--help"])
    assert exc.value.code == 0


def test_mudidi_top_level_help() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0


def test_mudidi_run_pdf_requires_dict_pages(tmp_path: Path) -> None:
    pdf = tmp_path / "dict.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    with pytest.raises(SystemExit, match="--dict-pages is required"):
        main(
            [
                "run",
                "--pages",
                str(pdf),
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )


def test_mudidi_run_rejects_dict_pages_for_directory(tmp_path: Path) -> None:
    snippets = tmp_path / "snippets"
    snippets.mkdir()
    with pytest.raises(SystemExit, match="only valid when --pages is a single PDF"):
        main(
            [
                "run",
                "--pages",
                str(snippets),
                "--dict-pages",
                "1-3",
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )


def test_mudidi_run_rejects_intro_with_pdf_pages(tmp_path: Path) -> None:
    pdf = tmp_path / "dict.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    with pytest.raises(SystemExit, match="--intro cannot be used when --pages is a PDF"):
        main(
            [
                "run",
                "--pages",
                str(pdf),
                "--dict-pages",
                "1-3",
                "--intro",
                str(pdf),
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )


def test_mudidi_run_rejects_intro_pages_for_directory(tmp_path: Path) -> None:
    snippets = tmp_path / "snippets"
    snippets.mkdir()
    with pytest.raises(SystemExit, match="only valid when --pages is a single PDF"):
        main(
            [
                "run",
                "--pages",
                str(snippets),
                "--intro-pages",
                "1-3",
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )
