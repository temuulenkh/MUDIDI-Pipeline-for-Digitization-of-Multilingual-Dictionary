"""
Parse SIL Toolbox MDF text files into DictionaryEntry-compatible dicts.

Each `\\lx` block is one lexical entry. Within a block:
- `\\se` introduces a subentry (child of the \\lx headword)
- `\\sn` introduces a numbered sense within the current section

Each (section × sense) combination becomes one output row.
"""
import re
from typing import Optional

_MARKER_RE = re.compile(r"^\\(\w+)\s*(.*)", re.UNICODE)

# Matches an inline marker boundary: optional whitespace (or immediately after a word char)
# + \word (1–4 lowercase letters) + whitespace or EOL.
# Handles both "\se alúghal \ps n." (space before) and "\lx aal\hm 1" (no space before).
_INLINE_MARKER_RE = re.compile(r"(?:[ \t]+|(?<=\S))(\\[a-z]{1,4})(?=[ \t]|$)", re.UNICODE)

# Markers that accumulate into lists
_LIST_MARKERS = {"xv", "xe", "xn", "cf"}

# Markers mapped to extra_fields keys
_EXTRA_FIELD_MAP = {
    "et": "etymology",
    "eg": "etymology",
    "ec": "etymology",
    "va": "variant_form",
    "mr": "morphemic_representation",
    "pd": "inflection",
    "ur": "dialect",
    "rf": "reference",
    "nt": "notes",
    "na": "notes",
    "so": "source",
    "ee": "encyclopedic_info",
    "sc": "scientific_name",
    "sd": "semantic_domain",
    "is": "semantic_domain",
    "th": "thesaurus",
    "sy": "synonym",
    "an": "antonym",
    "lf": "lexical_function",
    "re": "reverse_entry",
    "bb": "bibliography",
    "pc": "picture",
    "tb": "table",
    "st": "status",
    "dt": "date",
    "pl": "plural_form",
    "lt": "literal_meaning",
    "rd": "reduplication",
    "sg": "singular_form",
}

# Markers that are handled explicitly (canonical fields or _EXTRA_FIELD_MAP)
_CANONICAL_MARKERS = {
    "lx", "se", "sn", "hm", "ps", "ge", "de", "ph", "ue", "un",
    "xv", "xe", "xn", "cf",
    *_EXTRA_FIELD_MAP.keys(),
}


def _expand_inline_markers(line: str) -> list[str]:
    """Split a line that has multiple markers packed inline into one line per marker.

    The LLM occasionally emits subentry lines like:
        \\se alúghal \\ps n. \\de A ghost, spirit
    MDF requires each marker on its own line. This function splits such lines.
    """
    m = _MARKER_RE.match(line)
    if not m:
        return [line]
    parts = _INLINE_MARKER_RE.split(line)
    if len(parts) == 1:
        return [line]
    # parts alternates: [first_chunk, \\marker1, rest1, \\marker2, rest2, ...]
    expanded = [parts[0].rstrip()]
    for i in range(1, len(parts), 2):
        marker = parts[i]
        value = parts[i + 1].strip() if i + 1 < len(parts) else ""
        expanded.append(f"{marker} {value}".rstrip())
    return expanded


def _parse_markers(lines: list[str]) -> list[tuple[str, str]]:
    """Parse raw MDF lines into (marker, value) pairs, skipping blank lines."""
    result = []
    for line in lines:
        for expanded_line in _expand_inline_markers(line):
            m = _MARKER_RE.match(expanded_line)
            if m:
                result.append((m.group(1), m.group(2).strip()))
    return result


def _build_row(
    markers: list[tuple[str, str]],
    entry_type: str,
    headword: str,
    parent_lexeme: str,
    homonym_number: Optional[int],
    sense_number: Optional[int],
    source_page: str,
) -> dict:
    """Build one DictionaryEntry-compatible dict from a list of (marker, value) pairs."""
    row: dict = {
        "entry_type": entry_type,
        "headword": headword,
        "parent_lexeme": parent_lexeme,
        "homonym_number": homonym_number,
        "sense_number": sense_number,
        "gloss": "",
        "gloss_secondary": "",
        "usage_note": "",
        "pos": "",
        "phonetic": "",
        "cross_references": [],
        "examples": [],
        "example_glosses": [],
        "extra_fields": {},
        "_source_page": source_page,
    }

    has_ge = any(m == "ge" for m, _ in markers)

    for marker, value in markers:
        if not value:
            continue

        if marker == "ps":
            if row["pos"]:
                row["pos"] += " " + value
            else:
                row["pos"] = value
        elif marker == "ge":
            if not row["gloss"]:
                row["gloss"] = value
            elif not row["gloss_secondary"]:
                row["gloss_secondary"] = value
        elif marker == "de":
            if not has_ge:
                if not row["gloss"]:
                    row["gloss"] = value
                else:
                    row["gloss"] += " " + value
        elif marker in ("ue", "un"):
            if not row["usage_note"]:
                row["usage_note"] = value
            else:
                row["usage_note"] += "; " + value
        elif marker == "ph":
            row["phonetic"] = value
        elif marker == "xv":
            row["examples"].append(value)
        elif marker in ("xe", "xn"):
            row["example_glosses"].append(value)
        elif marker == "cf":
            row["cross_references"].append(value)
        elif marker in _EXTRA_FIELD_MAP:
            key = _EXTRA_FIELD_MAP[marker]
            if key in row["extra_fields"]:
                row["extra_fields"][key] += "; " + value
            else:
                row["extra_fields"][key] = value
        elif marker not in _CANONICAL_MARKERS:
            # Unknown marker → store as extra_fields[marker]
            if marker in row["extra_fields"]:
                row["extra_fields"][marker] += "; " + value
            else:
                row["extra_fields"][marker] = value

    return row


def _split_on_marker(
    pairs: list[tuple[str, str]], marker: str
) -> list[tuple[str, list[tuple[str, str]]]]:
    """
    Split a list of (marker, value) pairs on occurrences of `marker`.
    Returns [(value_at_split, subsequent_pairs), ...].
    The first segment (before the first occurrence) uses value="".
    """
    segments: list[tuple[str, list[tuple[str, str]]]] = []
    current_value = ""
    current: list[tuple[str, str]] = []
    started = False

    for m, v in pairs:
        if m == marker:
            if started:
                segments.append((current_value, current))
            current_value = v
            current = []
            started = True
        else:
            if not started:
                current.append((m, v))
            else:
                current.append((m, v))

    if started:
        segments.append((current_value, current))
    else:
        # marker never appeared — return the whole list as one "pre" segment
        segments = [("", current)]

    return segments


def _expand_senses(
    markers: list[tuple[str, str]],
    entry_type: str,
    headword: str,
    parent_lexeme: str,
    homonym_number: Optional[int],
    source_page: str,
) -> list[dict]:
    """
    Split markers on \\sn to produce one row per sense.
    If no \\sn present, produces a single row with sense_number=None.
    """
    rows = []
    # Collect markers before first \sn (shared header: ps, va, etc.)
    header: list[tuple[str, str]] = []
    sn_sections: list[tuple[int, list[tuple[str, str]]]] = []
    current_sn = None
    current_body: list[tuple[str, str]] = []

    for m, v in markers:
        if m == "sn":
            if current_sn is not None:
                sn_sections.append((current_sn, current_body))
            try:
                current_sn = int(v) if v.strip().isdigit() else None
            except (ValueError, AttributeError):
                current_sn = None
            current_body = []
        elif current_sn is None:
            header.append((m, v))
        else:
            current_body.append((m, v))

    if current_sn is not None:
        sn_sections.append((current_sn, current_body))

    if not sn_sections:
        rows.append(_build_row(
            header, entry_type, headword, parent_lexeme,
            homonym_number, None, source_page
        ))
    else:
        for sn, body in sn_sections:
            rows.append(_build_row(
                header + body, entry_type, headword, parent_lexeme,
                homonym_number, sn, source_page
            ))

    return rows


def _parse_block(
    pairs: list[tuple[str, str]], source_page: str
) -> list[dict]:
    """Parse one \\lx block into one or more rows."""
    if not pairs or pairs[0][0] != "lx":
        return []

    lx_value = pairs[0][1]
    rest = pairs[1:]

    # Extract homonym number
    homonym_number = None
    hm_pairs = [(m, v) for m, v in rest if m == "hm"]
    if hm_pairs:
        try:
            homonym_number = int(hm_pairs[0][1])
        except (ValueError, TypeError):
            pass

    # Split on \se to get main-entry section + subentry sections
    # First, collect everything before first \se
    main_pairs: list[tuple[str, str]] = []
    se_sections: list[tuple[str, list[tuple[str, str]]]] = []
    current_se = None
    current_body: list[tuple[str, str]] = []

    for m, v in rest:
        if m == "se":
            if current_se is not None:
                se_sections.append((current_se, current_body))
            current_se = v
            current_body = []
        elif current_se is None:
            main_pairs.append((m, v))
        else:
            current_body.append((m, v))

    if current_se is not None:
        se_sections.append((current_se, current_body))

    rows = []

    # Main entry rows (may be multiple if \sn present)
    rows.extend(_expand_senses(
        main_pairs, "main", lx_value, "", homonym_number, source_page
    ))

    # Subentry rows
    for se_headword, se_markers in se_sections:
        rows.extend(_expand_senses(
            se_markers, "subentry", se_headword, lx_value, None, source_page
        ))

    return rows


def parse_mdf_text(mdf_text: str, source_page: str = "") -> list[dict]:
    """
    Parse MDF text into a list of DictionaryEntry-compatible dicts.

    Args:
        mdf_text: Full contents of a .mdf.txt file.
        source_page: Label to attach to each row (e.g. "page_001").

    Returns:
        List of dicts with keys matching DictionaryEntry fields plus `_source_page`.
    """
    lines = mdf_text.splitlines()

    # Split into blocks on blank lines
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip() == "":
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)

    rows = []
    for block in blocks:
        pairs = _parse_markers(block)
        if not pairs:
            continue
        rows.extend(_parse_block(pairs, source_page))

    return rows
