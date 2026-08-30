"""Load and filter the project's attributed Unicode homoglyph data."""

from __future__ import annotations

import string
import unicodedata
from pathlib import Path
from typing import Iterable, Mapping

CODEBOX_SOURCE_URL = "https://github.com/codebox/homoglyph/blob/master/raw_data/chars.txt"
HOMOGLYPH_DATA_PATH = Path(__file__).with_name("data") / "codebox_ascii_homoglyphs.txt"

HOMOGLYPH_SETS = (
    "latin",
    "greek",
    "cyrillic",
    "armenian",
    "cherokee",
    "coptic",
    "canadian",
    "fullwidth",
    "mathematical",
    "other",
)

_NAME_MARKERS = {
    "latin": ("LATIN",),
    "greek": ("GREEK",),
    "cyrillic": ("CYRILLIC",),
    "armenian": ("ARMENIAN",),
    "cherokee": ("CHEROKEE",),
    "coptic": ("COPTIC",),
    "canadian": ("CANADIAN",),
    "fullwidth": ("FULLWIDTH",),
    "mathematical": ("MATHEMATICAL", "SCRIPT", "DOUBLE-STRUCK", "BLACK-LETTER"),
}


def _same_case_or_uncased(anchor: str, candidate: str) -> bool:
    if not anchor.isalpha() or candidate.lower() == candidate.upper():
        return True
    return anchor.isupper() == candidate.isupper()


def load_codebox_homoglyphs(path: Path = HOMOGLYPH_DATA_PATH) -> dict[str, tuple[str, ...]]:
    """Parse grouped characters into replacements for ASCII letters and digits."""
    mapping: dict[str, list[str]] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        anchors = [character for character in line if character in string.ascii_letters + string.digits]
        candidates = [character for character in line if character not in string.ascii_letters + string.digits]
        for anchor in anchors:
            replacements = mapping.setdefault(anchor, [])
            for candidate in candidates:
                if _same_case_or_uncased(anchor, candidate) and candidate not in replacements:
                    replacements.append(candidate)

    return {anchor: tuple(replacements) for anchor, replacements in mapping.items() if replacements}


def merge_homoglyph_maps(
    primary: Mapping[str, tuple[str, ...]],
    additional: Mapping[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    """Merge maps while preserving curated candidates first in candidate order."""
    merged = {key: list(values) for key, values in primary.items()}
    for key, values in additional.items():
        candidates = merged.setdefault(key, [])
        candidates.extend(value for value in values if value not in candidates)
    return {key: tuple(values) for key, values in merged.items()}


def homoglyph_sets(character: str) -> set[str]:
    """Return broad Unicode script/style labels for a replacement character."""
    name = unicodedata.name(character, "")
    labels = {
        label
        for label, markers in _NAME_MARKERS.items()
        if any(marker in name for marker in markers)
    }
    return labels or {"other"}


def _validate_sets(values: Iterable[str] | None) -> set[str]:
    normalized = {value.strip().lower() for value in values or () if value.strip()}
    unknown = normalized.difference(HOMOGLYPH_SETS)
    if unknown:
        raise ValueError(
            f"Unknown homoglyph set(s): {', '.join(sorted(unknown))}. "
            f"Supported sets: {', '.join(HOMOGLYPH_SETS)}"
        )
    return normalized


def filter_homoglyph_map(
    mapping: Mapping[str, tuple[str, ...]],
    include_sets: Iterable[str] | None = None,
    exclude_sets: Iterable[str] | None = None,
) -> dict[str, tuple[str, ...]]:
    """Filter replacements by Unicode script/style; exclusions take precedence."""
    included = _validate_sets(include_sets)
    excluded = _validate_sets(exclude_sets)
    filtered: dict[str, tuple[str, ...]] = {}

    for anchor, candidates in mapping.items():
        kept = tuple(
            candidate
            for candidate in candidates
            if (not included or homoglyph_sets(candidate).intersection(included))
            and not homoglyph_sets(candidate).intersection(excluded)
        )
        if kept:
            filtered[anchor] = kept
    return filtered
