"""Basic analysis and scoring for potentially obfuscated text."""

from __future__ import annotations

import string
import unicodedata
from dataclasses import dataclass

from adversarial.transformations import HOMOGLYPH_MAP, INVISIBLE_SPACING_CHARS, LEETSPEAK_MAP

CONFUSABLE_SET = {
    glyph
    for replacement in HOMOGLYPH_MAP.values()
    for glyph in (replacement if isinstance(replacement, tuple) else (replacement,))
}
LEET_SET = set(LEETSPEAK_MAP.values())


@dataclass
class AnalysisResult:
    normalized_text: str
    confusable_count: int
    invisible_count: int
    leetspeak_count: int
    punctuation_ratio: float
    score: float


def unicode_normalize(text: str, form: str = "NFKC") -> str:
    """Normalize text to reduce unicode obfuscation variance."""
    return unicodedata.normalize(form, text)


def detect_confusables(text: str) -> int:
    """Count known confusable homoglyph characters."""
    return sum(1 for ch in text if ch in CONFUSABLE_SET)


def detect_invisible_spacing(text: str) -> int:
    """Count known zero-width and discretionary separator characters."""
    return sum(1 for character in text if character in INVISIBLE_SPACING_CHARS)


def _punctuation_ratio(text: str) -> float:
    if not text:
        return 0.0
    punct = sum(1 for ch in text if ch in string.punctuation)
    return punct / len(text)


def suspicion_score(text: str) -> AnalysisResult:
    """
    Score text from 0 to 100 based on simple obfuscation markers.
    Higher means more suspiciously transformed.
    """
    normalized = unicode_normalize(text)
    confusables = detect_confusables(text)
    invisible_count = detect_invisible_spacing(text)
    leet_count = sum(1 for ch in text if ch in LEET_SET)
    punct_ratio = _punctuation_ratio(text)

    # Weighted linear score capped to 100 for easy interpretation.
    raw_score = (
        (confusables * 8.0)
        + (invisible_count * 8.0)
        + (leet_count * 4.0)
        + (punct_ratio * 100 * 1.5)
        + (abs(len(text) - len(normalized)) * 3.0)
    )
    score = max(0.0, min(100.0, raw_score))

    return AnalysisResult(
        normalized_text=normalized,
        confusable_count=confusables,
        invisible_count=invisible_count,
        leetspeak_count=leet_count,
        punctuation_ratio=punct_ratio,
        score=score,
    )
