"""Specialized document OCR / VLM backends for stage-1 raw extraction."""

from mudidi.ocr.vlm.registry import VLM_MODELS, get_vlm_spec, list_vlm_keys
from mudidi.ocr.vlm.runner import create_vlm_runner

__all__ = [
    "VLM_MODELS",
    "create_vlm_runner",
    "get_vlm_spec",
    "list_vlm_keys",
]
