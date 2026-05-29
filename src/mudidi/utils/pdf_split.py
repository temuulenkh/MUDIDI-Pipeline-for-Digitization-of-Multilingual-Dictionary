"""Split individual pages from a multi-page PDF using pdftk."""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_page_spec(spec: str) -> list[int]:
    """Expand a page specification into an ordered list of 1-based page numbers.

    Supports comma-separated singletons and hyphen-separated inclusive ranges,
    e.g. ``"97-123, 179-182"`` or ``"19, 83, 162"``. Returns ``[]`` for empty input.

    Raises:
        ValueError: When a token or range is malformed.
    """
    if not spec or not spec.strip():
        return []

    pages: list[int] = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            match = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", chunk)
            if not match:
                raise ValueError(f"Unrecognised page range: {chunk!r}")
            start, end = int(match.group(1)), int(match.group(2))
            if start < 1 or end < 1:
                raise ValueError(f"Page numbers must be >= 1: {chunk!r}")
            if end < start:
                raise ValueError(f"Descending range not supported: {chunk!r}")
            pages.extend(range(start, end + 1))
        else:
            if not chunk.isdigit():
                raise ValueError(f"Unrecognised page token: {chunk!r}")
            page = int(chunk)
            if page < 1:
                raise ValueError(f"Page numbers must be >= 1: {chunk!r}")
            pages.append(page)
    return pages


def pdftk_available() -> bool:
    """Return True when ``pdftk`` is on PATH."""
    return shutil.which("pdftk") is not None


def require_pdftk() -> None:
    """Raise ``RuntimeError`` when pdftk is missing."""
    if not pdftk_available():
        raise RuntimeError(
            "pdftk is not available on PATH. Install it to split PDF pages "
            "(e.g. apt install pdftk-java, or brew install pdftk-java)."
        )


def extract_single_page(source_pdf: Path, page: int, output_pdf: Path) -> None:
    """Extract a single 1-based page from ``source_pdf`` to ``output_pdf`` via pdftk."""
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "pdftk",
        str(source_pdf),
        "cat",
        str(page),
        "output",
        str(output_pdf),
    ]
    logger.debug("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            f"pdftk failed for {source_pdf.name} page {page}: {detail}"
        )


def extract_pdf_pages(
    source_pdf: Path,
    page_numbers: list[int],
    output_dir: Path,
    *,
    stem_template: str = "page_{page}.pdf",
    overwrite: bool = False,
) -> list[Path]:
    """Extract ``page_numbers`` from ``source_pdf`` into ``output_dir``.

    Output files are named ``page_{N}.pdf`` by default (``N`` = source PDF page
    number). Returns paths in the same order as ``page_numbers``.

    Time complexity: O(n) pdftk invocations for n pages.
    """
    require_pdftk()
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[Path] = []
    for page in page_numbers:
        out_path = output_dir / stem_template.format(page=page)
        if out_path.exists() and not overwrite:
            logger.debug("Reusing existing split page %s", out_path)
        else:
            extract_single_page(source_pdf, page, out_path)
        results.append(out_path)
    return results
