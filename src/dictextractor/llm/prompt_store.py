"""
Load LLM prompt templates from ``assets/PROMPT.md``.

Sections are delimited by level-2 markdown headers (``## section_id``). Edit the
markdown file to customize prompts at inference time; the store reloads when the
file modification time changes.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_SECTION_HEADER = re.compile(r"^## ([A-Za-z0-9_.-]+)\s*$")

_configured_path: Optional[Path] = None


def repo_root() -> Path:
    """Repository root (``MUDIDI/``)."""
    return Path(__file__).resolve().parents[3]


def default_prompts_path() -> Path:
    """Default path to ``assets/PROMPT.md``."""
    return repo_root() / "assets" / "PROMPT.md"


def configure_prompts(path: Path | str) -> None:
    """Set the prompts file used by :func:`get_prompt_store`."""
    global _configured_path
    resolved = Path(path).expanduser().resolve()
    _configured_path = resolved
    get_prompt_store().set_path(resolved)
    logger.info("Prompts file: %s", resolved)


def _resolve_prompts_path() -> Path:
    if _configured_path is not None:
        return _configured_path
    return default_prompts_path()


def parse_prompt_sections(text: str) -> Dict[str, str]:
    """
    Parse ``## section_id`` blocks from markdown text.

    Time: O(n) in file length.
    """
    sections: Dict[str, str] = {}
    current_id: Optional[str] = None
    current_lines: list[str] = []

    for line in text.splitlines():
        match = _SECTION_HEADER.match(line)
        if match:
            if current_id is not None:
                sections[current_id] = "\n".join(current_lines).strip("\n")
            current_id = match.group(1)
            current_lines = []
            continue
        if current_id is not None:
            current_lines.append(line)

    if current_id is not None:
        sections[current_id] = "\n".join(current_lines).strip("\n")

    return sections


class PromptStore:
    """Cached reader for ``PROMPT.md`` with mtime-based invalidation."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = path or _resolve_prompts_path()
        self._signature: Optional[tuple[float, int]] = None
        self._sections: Dict[str, str] = {}

    def set_path(self, path: Path) -> None:
        """Point at a different prompts file and force reload."""
        self._path = path
        self._signature = None
        self._sections = {}

    @property
    def path(self) -> Path:
        return self._path

    def _reload_if_changed(self) -> None:
        if not self._path.is_file():
            raise FileNotFoundError(
                f"Prompts file not found: {self._path}. "
                "Create it or pass --prompts-file to dictextractor extract."
            )
        stat = self._path.stat()
        signature = (stat.st_mtime, stat.st_size)
        if signature == self._signature and self._sections:
            return
        text = self._path.read_text(encoding="utf-8")
        self._sections = parse_prompt_sections(text)
        self._signature = signature
        logger.debug("Loaded %d prompt sections from %s", len(self._sections), self._path)

    def section_ids(self) -> list[str]:
        """Return loaded section identifiers."""
        self._reload_if_changed()
        return sorted(self._sections)

    def get(self, section_id: str) -> str:
        """Return raw section text (no placeholder substitution)."""
        self._reload_if_changed()
        try:
            return self._sections[section_id]
        except KeyError as exc:
            available = ", ".join(sorted(self._sections))
            raise KeyError(
                f"Prompt section {section_id!r} not found in {self._path}. "
                f"Available: {available}"
            ) from exc

    def format(self, section_id: str, **kwargs: object) -> str:
        """Return section text with ``str.format`` placeholders filled."""
        template = self.get(section_id)
        if not kwargs:
            return template
        return template.format(**kwargs)


_store: Optional[PromptStore] = None


def get_prompt_store() -> PromptStore:
    """Return the process-wide prompt store."""
    global _store
    if _store is None:
        _store = PromptStore(_resolve_prompts_path())
    return _store
