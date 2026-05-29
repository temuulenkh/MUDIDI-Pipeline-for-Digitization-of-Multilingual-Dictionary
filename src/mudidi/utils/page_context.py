"""Neighbor page context for inference-mode extraction."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from mudidi.utils.stage2_page_selection import sort_snippet_pages

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NeighborPage:
    """One adjacent dictionary page used as layout context."""

    stem: str
    image_path: Path
    transcript: str = ""


@dataclass(frozen=True)
class PageContext:
    """Previous and next page context for the current snippet."""

    previous: Optional[NeighborPage]
    next: Optional[NeighborPage]
    current_stem: str

    @property
    def has_neighbors(self) -> bool:
        return self.previous is not None or self.next is not None


TranscriptLoader = Callable[[str], str]


def _empty_loader(_stem: str) -> str:
    return ""


def resolve_page_context(
    pages: list[Path],
    index: int,
    *,
    transcript_loader: TranscriptLoader | None = None,
) -> PageContext:
    """
    Build neighbor context for ``pages[index]``.

    Args:
        pages: Snippet page paths in the caller's processing order.
        index: Index of the current page in ``pages`` (same list passed to the loop).
        transcript_loader: Optional callback ``stem -> transcript text`` for
            pages already processed in the current run.
    """
    loader = transcript_loader or _empty_loader
    ordered = sort_snippet_pages(pages)
    current = pages[index]
    try:
        pos = next(i for i, p in enumerate(ordered) if p == current)
    except StopIteration as exc:
        raise ValueError(
            f"Page {current} at index {index} not found in sorted snippet list."
        ) from exc
    stem = current.stem

    previous: Optional[NeighborPage] = None
    next_page: Optional[NeighborPage] = None

    if pos > 0:
        prev_path = ordered[pos - 1]
        previous = NeighborPage(
            stem=prev_path.stem,
            image_path=prev_path,
            transcript=loader(prev_path.stem),
        )
    if pos + 1 < len(ordered):
        nxt_path = ordered[pos + 1]
        next_page = NeighborPage(
            stem=nxt_path.stem,
            image_path=nxt_path,
            transcript=loader(nxt_path.stem),
        )

    return PageContext(previous=previous, next=next_page, current_stem=stem)


def format_neighbor_text_block(
    page: Optional[NeighborPage],
    *,
    label: str,
) -> str:
    """Format a neighbor page as a text block for prompt injection."""
    if page is None:
        return f"<{label}>\n(none)\n</{label}>"
    transcript = page.transcript.strip()
    transcript_section = (
        f"\n<transcript>\n{transcript}\n</transcript>" if transcript else ""
    )
    return (
        f"<{label}>\n"
        f"page: {page.stem}\n"
        f"Use this page only for entry-boundary context.{transcript_section}\n"
        f"</{label}>"
    )


def format_page_boundary_rules() -> str:
    """Shared boundary instructions for inference prompts."""
    return (
        "Page boundary rules:\n"
        "- Output only content that belongs to the CURRENT page.\n"
        "- INCLUDE entries that START on the current page even if they continue "
        "onto the next page.\n"
        "- EXCLUDE entries that STARTED on the previous page and only continue "
        "on the current page.\n"
        "- Neighbor pages are context for disambiguation only; do not transcribe "
        "their full text into the current page output."
    )
