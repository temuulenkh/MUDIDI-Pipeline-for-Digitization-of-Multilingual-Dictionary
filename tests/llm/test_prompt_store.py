"""Tests for assets/PROMPT.json loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mudidi.llm.prompt_mode import resolve_prompt_id
from mudidi.llm.prompt_store import (
    PromptDefinition,
    PromptStore,
    PromptVariable,
    configure_prompts,
    default_prompts_path,
    parse_prompt_file,
)


@pytest.fixture(autouse=True)
def _use_default_prompts() -> None:
    configure_prompts(default_prompts_path())


def test_default_prompts_file_exists() -> None:
    path = default_prompts_path()
    assert path.is_file(), f"Missing default prompts file: {path}"


def test_parse_prompt_file() -> None:
    payload = {
        "alpha": {
            "prompt": "Hello {name}",
            "variables": [
                {
                    "name": "name",
                    "tag": None,
                    "description": "Greeting target.",
                }
            ],
        },
        "beta": {"prompt": "Second section", "variables": []},
    }
    prompts = parse_prompt_file(json.dumps(payload))
    assert prompts["alpha"].prompt == "Hello {name}"
    assert prompts["alpha"].variables[0].name == "name"
    assert prompts["beta"].prompt == "Second section"


def test_prompt_store_reload_on_mtime(tmp_path: Path) -> None:
    path = tmp_path / "PROMPT.json"
    path.write_text(
        json.dumps({"test": {"prompt": "first", "variables": []}}),
        encoding="utf-8",
    )
    store = PromptStore(path)
    assert store.get("test") == "first"

    path.write_text(
        json.dumps({"test": {"prompt": "second", "variables": []}}),
        encoding="utf-8",
    )
    assert store.get("test") == "second"


def test_required_stage_prompts_present() -> None:
    store = PromptStore(default_prompts_path())
    required = (
        "stage_1_system",
        "stage_1_flat_system_benchmark",
        "stage_1_flat_system_inference",
        "stage_1_user_alphabet",
        "stage_1_user_ocr_reference",
        "stage_1_user_closing",
        "mdf_marker_reference",
        "stage_2_discovery_system",
        "stage_2_discovery_user",
        "stage_2_direct_mdf_system_benchmark",
        "stage_2_direct_mdf_system_inference",
        "stage_2_direct_mdf_user_benchmark",
        "stage_2_direct_mdf_user_inference",
    )
    for prompt_id in required:
        assert store.get(prompt_id), f"Empty prompt: {prompt_id}"


def test_resolve_prompt_id_by_mode() -> None:
    assert resolve_prompt_id("stage_1_flat_system", "benchmark").endswith("_benchmark")
    assert resolve_prompt_id("stage_1_flat_system", "inference").endswith("_inference")


def test_stage_1_alphabet_variables() -> None:
    store = PromptStore(default_prompts_path())
    variables = store.variables("stage_1_user_alphabet")
    assert len(variables) == 1
    assert variables[0].name == "alphabet_text"
    assert variables[0].tag == "<alphabet>"


def test_stage_2_discovery_user_formats_transcription() -> None:
    store = PromptStore(default_prompts_path())
    rendered = store.format(
        "stage_2_discovery_user",
        transcription="sample line",
        config_hint="",
    )
    assert "<sample_transcription>" in rendered
    assert "sample line" in rendered


def test_pass_1_does_not_accept_toolbox_pdf() -> None:
    src = (
        Path(__file__).resolve().parents[2] / "src/mudidi/llm/pass_1.py"
    ).read_text(encoding="utf-8")
    fn_block = src.split("def discover_field_cheatsheet", 1)[1].split("\ndef ", 1)[0]
    assert "toolbox_pdf" not in fn_block


def test_prompt_definition_model() -> None:
    definition = PromptDefinition(
        prompt="Hi {user}",
        variables=[
            PromptVariable(name="user", tag=None, description="Recipient name."),
        ],
    )
    assert definition.variables[0].description == "Recipient name."


def test_materialize_zip_resource_prompts(tmp_path: Path, monkeypatch) -> None:
    from mudidi.llm import prompt_store

    prompt_store._bundled_prompts_cache = None
    payload = {"demo": {"prompt": "Hello", "variables": []}}

    class FakeRef:
        def read_text(self, encoding: str = "utf-8") -> str:
            return json.dumps(payload)

    class FakeFiles:
        def joinpath(self, *_parts: str) -> FakeRef:
            return FakeRef()

    monkeypatch.setattr(
        prompt_store.resources,
        "files",
        lambda _pkg: FakeFiles(),
    )
    monkeypatch.setattr(
        prompt_store,
        "package_root",
        lambda: tmp_path / "missing_pkg_assets",
    )
    monkeypatch.setattr(
        prompt_store,
        "repo_root",
        lambda: tmp_path / "missing_repo_assets",
    )
    monkeypatch.setenv("TMPDIR", str(tmp_path))

    path = prompt_store._materialize_zip_resource_prompts()
    assert path.is_file()
    assert json.loads(path.read_text(encoding="utf-8")) == payload

    path_again = prompt_store._materialize_zip_resource_prompts()
    assert path_again == path
    prompt_store._bundled_prompts_cache = None
