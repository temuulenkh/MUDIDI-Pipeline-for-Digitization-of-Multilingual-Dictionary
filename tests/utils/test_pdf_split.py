"""Tests for PDF page splitting helpers."""

from __future__ import annotations

import pytest

from mudidi.utils.pdf_split import parse_page_spec


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        ("", []),
        ("   ", []),
        ("5", [5]),
        ("1,3,5", [1, 3, 5]),
        ("1-3", [1, 2, 3]),
        ("97 - 123, 179 - 182", list(range(97, 124)) + list(range(179, 183))),
    ],
)
def test_parse_page_spec(spec: str, expected: list[int]) -> None:
    assert parse_page_spec(spec) == expected


@pytest.mark.parametrize(
    "spec",
    ["1-", "a-b", "0-1", "3-1", "x"],
)
def test_parse_page_spec_invalid(spec: str) -> None:
    with pytest.raises(ValueError):
        parse_page_spec(spec)
