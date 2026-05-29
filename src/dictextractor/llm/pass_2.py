"""
Pass 2: direct page transcription → Toolbox MDF text using a field profile.

Used by ``TwoStageLLMExtraction`` for Stage 2 MDF output.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Optional

from dictextractor.llm import client as llm
from dictextractor.llm.prompt_store import get_prompt_store
from dictextractor.schemas.field_map import FieldMapPrompt
from dictextractor.utils.image import image_data_url, resolve_mime_type
from dictextractor.utils.mdf_export import normalize_mdf_text
from dictextractor.utils.pdf_render import needs_pdf_rasterization

logger = logging.getLogger(__name__)


def direct_mdf_system_prompt() -> str:
    """Pass 2 direct MDF system prompt."""
    return get_prompt_store().get("stage_2_direct_mdf_system")


def strip_markdown_fences(text: str) -> str:
    """Remove optional markdown code fences from model output."""
    text = text.strip()
    fence = re.search(r"```(?:mdf|text)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        return fence.group(1).strip()
    return text


def _toolbox_content_parts(
    toolbox_pdf: Path,
    *,
    model: str,
) -> tuple[str, list[dict]]:
    """Build prompt section and optional vision parts for the Toolbox MDF manual."""
    store = get_prompt_store()
    if needs_pdf_rasterization(model):
        # OpenRouter / OpenAI cannot ingest PDF; attaching every rasterized page
        # (~65 images) routinely blows prompt limits and causes empty API responses.
        logger.info(
            "Toolbox PDF %s attached as text reference for model %s",
            toolbox_pdf.name,
            model,
        )
        section = store.format(
            "stage_2_toolbox_text_section",
            mdf_marker_reference=store.get("mdf_marker_reference"),
        )
        return section, []

    section = store.get("stage_2_toolbox_pdf_section")
    return section, [
        {
            "type": "image_url",
            "image_url": {
                "url": image_data_url(str(toolbox_pdf), "application/pdf"),
            },
        }
    ]


def build_direct_mdf_messages(
    *,
    transcription: str,
    image_path: str,
    intro_image_paths: List[str],
    field_map: FieldMapPrompt,
    model: str,
    guides: str = "",
    toolbox_pdf: Optional[Path] = None,
) -> list[dict]:
    """Build LLM messages for Pass 2 direct MDF extraction."""
    guides_block = f"\n\nUSER DEFINED GUIDELINES\n{guides}" if guides.strip() else ""
    toolbox_section = ""
    toolbox_parts: list[dict] = []
    if toolbox_pdf and toolbox_pdf.is_file():
        toolbox_section, toolbox_parts = _toolbox_content_parts(
            toolbox_pdf,
            model=model,
        )
    user_text = get_prompt_store().format(
        "stage_2_direct_mdf_user",
        transcription=transcription.strip(),
        field_block=field_map.format_prompt_block(),
        guides_block=guides_block,
        toolbox_section=toolbox_section,
    )
    mime = resolve_mime_type(image_path)
    content: list[dict] = [{"type": "text", "text": user_text}]
    content.append(
        {
            "type": "image_url",
            "image_url": {"url": image_data_url(image_path, mime)},
        }
    )
    for intro_img in intro_image_paths:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": image_data_url(intro_img, resolve_mime_type(intro_img))
                },
            }
        )
    content.extend(toolbox_parts)
    return [
        {"role": "system", "content": direct_mdf_system_prompt()},
        {"role": "user", "content": content},
    ]


def extract_direct_mdf(
    *,
    transcription: str,
    image_path: str,
    intro_image_paths: List[str],
    field_map: FieldMapPrompt,
    model: str,
    reasoning_effort: str,
    guides: str = "",
    toolbox_pdf: Optional[Path] = None,
) -> tuple[str, str, dict, list]:
    """
    Run Pass 2 direct MDF extraction.

    Returns:
        (mdf_text, raw_response, usage_dict, sanitized_messages)
    """
    messages = build_direct_mdf_messages(
        transcription=transcription,
        image_path=image_path,
        intro_image_paths=intro_image_paths,
        field_map=field_map,
        model=model,
        guides=guides,
        toolbox_pdf=toolbox_pdf,
    )
    raw, usage = llm.complete_with_usage(
        model=model,
        messages=messages,
        reasoning_effort=reasoning_effort,  # type: ignore[arg-type]
    )
    mdf_text = normalize_mdf_text(strip_markdown_fences(raw))
    return mdf_text, raw, usage, messages
