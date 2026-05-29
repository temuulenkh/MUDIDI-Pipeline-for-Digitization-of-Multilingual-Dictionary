"""
Stage 1 prompt builders.

Templates live in ``assets/PROMPT.json``; this module assembles dynamic user turns.
"""

from __future__ import annotations

from mudidi.config.run_config import PromptMode
from mudidi.llm.prompt_mode import resolve_prompt_id
from mudidi.llm.prompt_store import get_prompt_store
from mudidi.utils.page_context import (
    PageContext,
    format_neighbor_text_block,
    format_page_boundary_rules,
)


def stage_1_system_prompt(mode: PromptMode = "benchmark") -> str:
    """Stage 1 column-mode system prompt."""
    return get_prompt_store().get("stage_1_system")


def stage_1_flat_system_prompt(
    mode: PromptMode = "benchmark",
    page_context: PageContext | None = None,
) -> str:
    """Stage 1 flat-mode system prompt."""
    store = get_prompt_store()
    prompt_id = resolve_prompt_id("stage_1_flat_system", mode)
    if mode == "inference" and page_context is not None:
        return store.format(
            prompt_id,
            page_boundary_rules=format_page_boundary_rules(),
            previous_page_context=format_neighbor_text_block(
                page_context.previous, label="previous_page"
            ),
            next_page_context=format_neighbor_text_block(
                page_context.next, label="next_page"
            ),
        )
    return store.get(prompt_id)


def stage_1_user(
    alphabet_text: str = "",
    ocr_hint: str = "",
    guides: str = "",
) -> str:
    """
    Build the user-turn prompt for Stage 1 transcription.

    Args:
        alphabet_text: The alphabet/legend for the script (text form).
        ocr_hint: Optional existing OCR output as a character-shape reference.
        guides: Optional user-defined guidelines appended verbatim at the end.
    """
    store = get_prompt_store()
    parts: list[str] = []
    if alphabet_text:
        parts.append(store.format("stage_1_user_alphabet", alphabet_text=alphabet_text))
    if ocr_hint:
        parts.append(store.format("stage_1_user_ocr_reference", ocr_hint=ocr_hint))
    parts.append(store.get("stage_1_user_closing"))
    if guides:
        parts.append(f"USER DEFINED GUIDELINES\n{guides}")
    return "\n\n".join(parts)


def stage_1_neighbor_image_urls(page_context: PageContext | None) -> list[str]:
    """Return data URLs for neighbor page images (inference mode)."""
    if page_context is None:
        return []
    from mudidi.utils.image import image_data_url, resolve_mime_type

    urls: list[str] = []
    for neighbor in (page_context.previous, page_context.next):
        if neighbor is None:
            continue
        mime = resolve_mime_type(str(neighbor.image_path))
        urls.append(image_data_url(str(neighbor.image_path), mime))
    return urls
