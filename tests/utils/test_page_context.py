"""Tests for neighbor page context resolution."""

from __future__ import annotations

from pathlib import Path

from mudidi.utils.page_context import (
    format_neighbor_text_block,
    format_page_boundary_rules,
    resolve_page_context,
)


def test_resolve_page_context_middle_page(tmp_path: Path) -> None:
    pages = [
        tmp_path / "page_1.png",
        tmp_path / "page_2.png",
        tmp_path / "page_3.png",
    ]
    for page in pages:
        page.write_bytes(b"png")

    ctx = resolve_page_context(pages, 1, transcript_loader=lambda s: f"text-{s}")
    assert ctx.current_stem == "page_2"
    assert ctx.previous is not None
    assert ctx.previous.stem == "page_1"
    assert ctx.previous.transcript == "text-page_1"
    assert ctx.next is not None
    assert ctx.next.stem == "page_3"


def test_resolve_page_context_first_page(tmp_path: Path) -> None:
    pages = [tmp_path / "page_1.png", tmp_path / "page_2.png"]
    for page in pages:
        page.write_bytes(b"png")
    ctx = resolve_page_context(pages, 0)
    assert ctx.previous is None
    assert ctx.next is not None


def test_resolve_page_context_lexicographic_caller_index(tmp_path: Path) -> None:
    """Index follows caller list order; neighbors follow numeric page order."""
    pages_lex = [
        tmp_path / "page_1.png",
        tmp_path / "page_10.png",
        tmp_path / "page_2.png",
    ]
    for page in pages_lex:
        page.write_bytes(b"png")

    ctx = resolve_page_context(pages_lex, 1)
    assert ctx.current_stem == "page_10"
    assert ctx.previous is not None
    assert ctx.previous.stem == "page_2"
    assert ctx.next is None


def test_format_neighbor_and_boundary_rules() -> None:
    block = format_neighbor_text_block(None, label="previous_page")
    assert "<previous_page>" in block
    assert "(none)" in block
    rules = format_page_boundary_rules()
    assert "CURRENT page" in rules
    assert "INCLUDE entries that START on the current page" in rules
