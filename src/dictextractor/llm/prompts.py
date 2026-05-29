"""
Stage 1 prompt builders.

Templates live in ``assets/PROMPT.md``; this module assembles dynamic user turns.
"""

from dictextractor.llm.prompt_store import get_prompt_store


def stage_1_system_prompt() -> str:
    """Stage 1 column-mode system prompt."""
    return get_prompt_store().get("stage_1_system")


def stage_1_flat_system_prompt() -> str:
    """Stage 1 flat-mode system prompt."""
    return get_prompt_store().get("stage_1_flat_system")


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
