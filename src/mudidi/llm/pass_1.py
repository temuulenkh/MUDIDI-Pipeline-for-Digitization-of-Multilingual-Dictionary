"""
Pass 1: discover which MDF markers this dictionary uses.

Output is a compact marker list + structure rules (parse rules). Cached per stage-2
experiment as ``outputs/stage-2/<experiment>/parse-rules.json``.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import List, Optional

from mudidi.llm.client import complete
from mudidi.llm.prompt_store import get_prompt_store
from mudidi.paths import LEGACY_PARSE_RULES_FILENAME, PARSE_RULES_FILENAME
from mudidi.schemas.dictionary_languages import DictionaryLanguagesConfig
from mudidi.schemas.field_cheatsheet import DictionaryMarkerCheatsheet
from mudidi.utils.image import image_data_url, resolve_mime_type

logger = logging.getLogger(__name__)


def resolve_parse_rules_read_path(directory: Path) -> Path:
    """Return an existing parse-rules file (new name, then legacy benchmark gold name)."""
    new_path = directory / PARSE_RULES_FILENAME
    if new_path.is_file():
        return new_path
    legacy = directory / LEGACY_PARSE_RULES_FILENAME
    if legacy.is_file():
        return legacy
    return new_path


def pass_1_system_prompt() -> str:
    """Pass 1 field-discovery system prompt."""
    store = get_prompt_store()
    return store.format(
        "stage_2_pass_1",
        mdf_marker_reference=store.get("mdf_marker_reference"),
    )


def _extract_json_object(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in field discovery response.")
    return json.loads(text[start : end + 1])


def _config_hint(config: Optional[DictionaryLanguagesConfig]) -> str:
    if config is None:
        return ""
    target_names = ", ".join(t.language for t in config.targets)
    return (
        f"\n3. Language roles: layout={config.layout}, "
        f"source={config.source.language}, targets=[{target_names}].\n"
    )


def discover_field_cheatsheet(
    *,
    transcription: str,
    sample_image: Path,
    intro_images: List[Path],
    model: str,
    reasoning_effort: str = "high",
    languages_config: Optional[DictionaryLanguagesConfig] = None,
    dictionary_name: str = "",
) -> DictionaryMarkerCheatsheet:
    """Pass 1: discover markers + rules for this dictionary."""
    user_text = get_prompt_store().format(
        "stage_2_pass_2",
        transcription=transcription.strip(),
        config_hint=_config_hint(languages_config),
    )
    content: list[dict] = [{"type": "text", "text": user_text}]
    for intro_img in intro_images:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": image_data_url(str(intro_img), resolve_mime_type(str(intro_img)))
                },
            }
        )
    content.append(
        {
            "type": "image_url",
            "image_url": {
                "url": image_data_url(str(sample_image), resolve_mime_type(str(sample_image)))
            },
        }
    )
    messages = [
        {"role": "system", "content": pass_1_system_prompt()},
        {"role": "user", "content": content},
    ]
    logger.info("Pass 1 field discovery: model=%s sample=%s", model, sample_image.name)
    raw = complete(model=model, messages=messages, reasoning_effort=reasoning_effort)  # type: ignore[arg-type]
    data = _extract_json_object(raw)
    sheet = DictionaryMarkerCheatsheet.model_validate(data)
    if dictionary_name and not sheet.dictionary_name:
        sheet = sheet.model_copy(update={"dictionary_name": dictionary_name})
    return sheet


def gold_parse_rules_path(entry_dir: Path) -> Path:
    """Resolve human-authored parse rules under ``outputs/stage-2-gold/``."""
    gold_dir = entry_dir / "outputs" / "stage-2-gold"
    return resolve_parse_rules_read_path(gold_dir)


def gold_cheatsheet_path(entry_dir: Path) -> Path:
    """Deprecated alias for :func:`gold_parse_rules_path`."""
    return gold_parse_rules_path(entry_dir)


def load_gold_parse_rules(entry_dir: Path) -> DictionaryMarkerCheatsheet:
    """Load gold Pass-1 parse rules for a dictionary entry."""
    path = gold_parse_rules_path(entry_dir)
    if not path.is_file():
        raise FileNotFoundError(
            f"Gold parse rules not found under {entry_dir / 'outputs' / 'stage-2-gold'} "
            f"(tried {PARSE_RULES_FILENAME} and {LEGACY_PARSE_RULES_FILENAME})"
        )
    logger.info("Loading gold parse rules: %s", path)
    return DictionaryMarkerCheatsheet.model_validate_json(path.read_text(encoding="utf-8"))


def load_gold_cheatsheet(entry_dir: Path) -> DictionaryMarkerCheatsheet:
    """Deprecated alias for :func:`load_gold_parse_rules`."""
    return load_gold_parse_rules(entry_dir)


def load_or_discover_parse_rules(
    cache_path: Path,
    *,
    force_refresh: bool = False,
    **discover_kwargs,
) -> DictionaryMarkerCheatsheet:
    """Load cached parse rules or run Pass 1 and save."""
    read_path = resolve_parse_rules_read_path(cache_path.parent)
    if read_path.is_file() and not force_refresh:
        logger.info("Loading cached parse rules: %s", read_path)
        return DictionaryMarkerCheatsheet.model_validate_json(
            read_path.read_text(encoding="utf-8")
        )
    sheet = discover_field_cheatsheet(**discover_kwargs)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(sheet.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Saved parse rules → %s", cache_path)
    return sheet


def load_or_discover_cheatsheet(
    cache_path: Path,
    *,
    force_refresh: bool = False,
    **discover_kwargs,
) -> DictionaryMarkerCheatsheet:
    """Deprecated alias for :func:`load_or_discover_parse_rules`."""
    return load_or_discover_parse_rules(cache_path, force_refresh=force_refresh, **discover_kwargs)
