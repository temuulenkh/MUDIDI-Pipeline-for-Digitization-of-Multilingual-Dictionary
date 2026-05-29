"""Tests for mudidi CLI argument wiring."""

from __future__ import annotations

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
