"""Tests for multi-sample Pass 1 parse-rules discovery."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from mudidi.llm.pass_1 import discover_field_cheatsheet_multi, load_parse_rules_file
from mudidi.schemas.field_cheatsheet import DictionaryMarkerCheatsheet, MarkerLine


def test_load_parse_rules_file(tmp_path: Path) -> None:
    path = tmp_path / "parse-rules.json"
    path.write_text(
        DictionaryMarkerCheatsheet(
            dictionary_name="Test",
            markers=[MarkerLine(marker="lx", description="headword")],
        ).model_dump_json(indent=2),
        encoding="utf-8",
    )
    loaded = load_parse_rules_file(path)
    assert loaded.dictionary_name == "Test"
    assert loaded.markers[0].marker == "lx"


@patch("mudidi.llm.pass_1.complete")
def test_discover_field_cheatsheet_multi_uses_multi_prompt(mock_complete) -> None:
    mock_complete.return_value = (
        '{"dictionary_name": "Test", "markers": [{"marker": "lx", "description": "hw"}], '
        '"rules": [], "abbreviations": {}}'
    )
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        png1 = tmp_path / "page_1.png"
        png2 = tmp_path / "page_2.png"
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05"
            b"\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        png1.write_bytes(png_bytes)
        png2.write_bytes(png_bytes)

        sheet = discover_field_cheatsheet_multi(
            samples=[
                ("page_1", "line one", png1),
                ("page_2", "line two", png2),
            ],
            intro_images=[],
            model="gemini/gemini-3-flash-preview",
        )

    assert sheet.dictionary_name == "Test"
    user_content = mock_complete.call_args.kwargs["messages"][1]["content"]
    text_part = user_content[0]["text"]
    assert "Several sample dictionary pages" in text_part
    assert '<sample_transcription page="page_1">' in text_part
    assert '<sample_transcription page="page_2">' in text_part
    assert len(user_content) == 3  # text + two sample images
