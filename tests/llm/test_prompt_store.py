"""Tests for assets/PROMPT.md loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from dictextractor.llm.prompt_store import (
    PromptStore,
    configure_prompts,
    default_prompts_path,
    parse_prompt_sections,
)


@pytest.fixture(autouse=True)
def _use_default_prompts() -> None:
    configure_prompts(default_prompts_path())


def test_default_prompts_file_exists() -> None:
    path = default_prompts_path()
    assert path.is_file(), f"Missing default prompts file: {path}"


def test_parse_prompt_sections() -> None:
    text = """# Title

Intro paragraph.

## alpha

Hello {name}

## beta

Second section
"""
    sections = parse_prompt_sections(text)
    assert sections["alpha"] == "Hello {name}"
    assert sections["beta"] == "Second section"


def test_prompt_store_reload_on_mtime(tmp_path: Path) -> None:
    path = tmp_path / "PROMPT.md"
    path.write_text("## test\nfirst\n", encoding="utf-8")
    store = PromptStore(path)
    assert store.get("test") == "first"

    path.write_text("## test\nsecond\n", encoding="utf-8")
    assert store.get("test") == "second"


def test_required_stage_sections_present() -> None:
    store = PromptStore(default_prompts_path())
    required = (
        "stage_1_system",
        "stage_1_flat_system",
        "stage_1_user_alphabet",
        "stage_1_user_ocr_reference",
        "stage_1_user_closing",
        "mdf_marker_reference",
        "stage_2_discovery_system",
        "stage_2_discovery_user",
        "stage_2_direct_mdf_system",
        "stage_2_direct_mdf_user",
    )
    for section_id in required:
        assert store.get(section_id), f"Empty section: {section_id}"


def test_stage_2_discovery_user_formats_transcription() -> None:
    store = PromptStore(default_prompts_path())
    rendered = store.format(
        "stage_2_discovery_user",
        transcription="sample line",
        config_hint="",
    )
    assert "<sample_transcription>" in rendered
    assert "sample line" in rendered


def test_mdf_marker_reference_in_prompt_file() -> None:
    ref = PromptStore(default_prompts_path()).get("mdf_marker_reference")
    for marker in ("lx", "gn", "ge", "sn", "hm", "se", "un", "de", "dn", "cf", "ps", "ph"):
        assert marker in ref
    assert "\\1s" not in ref
    assert "e=English, n=national, r=regional, v=vernacular" in ref


def test_pass_1_does_not_accept_toolbox_pdf() -> None:
    src = (
        Path(__file__).resolve().parents[2] / "src/dictextractor/llm/pass_1.py"
    ).read_text(encoding="utf-8")
    fn_block = src.split("def discover_field_cheatsheet", 1)[1].split("\ndef ", 1)[0]
    assert "toolbox_pdf" not in fn_block
