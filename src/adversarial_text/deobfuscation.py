"""Best-effort recovery of text transformed by common obfuscation techniques."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from .transformations import (
    HOMOGLYPH_MAP,
    INVISIBLE_SPACING_CHARS,
    LEETSPEAK_MAP,
    PUNCTUATION_NOISE,
)

from .scoring import suspicion_score

DecodeLevel = Literal["conservative", "aggressive"]


@dataclass(frozen=True)
class DeobfuscationChange:
    """One auditable change made while recovering a candidate."""

    index: int
    category: str
    original: str
    replacement: str
    confidence: float
    explanation: str


@dataclass(frozen=True)
class DeobfuscationResult:
    """Recovered candidates, scores, and an audit trail."""

    original_text: str
    best_candidate: str
    alternatives: list[str]
    changes: list[DeobfuscationChange]
    input_suspicion_score: float
    residual_suspicion_score: float
    recovery_confidence: float
    suspicion_reduction: float
    unresolved_markers: int
    warnings: list[str]


def _reverse_map(mapping: dict[str, str | tuple[str, ...]]) -> dict[str, tuple[str, ...]]:
    reversed_values: dict[str, list[str]] = {}
    for original, replacements in mapping.items():
        values = replacements if isinstance(replacements, tuple) else (replacements,)
        for replacement in values:
            reversed_values.setdefault(replacement, []).append(original)
    return {replacement: tuple(originals) for replacement, originals in reversed_values.items()}


HOMOGLYPH_REVERSE_MAP = _reverse_map(HOMOGLYPH_MAP)
LEETSPEAK_REVERSE_MAP = _reverse_map(LEETSPEAK_MAP)
_NOISE_SET = set(PUNCTUATION_NOISE)
_INVISIBLE_SET = set(INVISIBLE_SPACING_CHARS)


def _remove_invisible_spacing(text: str) -> tuple[str, list[DeobfuscationChange]]:
    output: list[str] = []
    changes: list[DeobfuscationChange] = []
    for index, character in enumerate(text):
        if character not in _INVISIBLE_SET:
            output.append(character)
            continue
        changes.append(
            DeobfuscationChange(
                index=index,
                category="invisible_spacing",
                original=character,
                replacement="",
                confidence=0.99,
                explanation="Removed a zero-width or discretionary separator.",
            )
        )
    return "".join(output), changes


def _unicode_normalize(text: str) -> tuple[str, list[DeobfuscationChange]]:
    output: list[str] = []
    changes: list[DeobfuscationChange] = []
    for index, character in enumerate(text):
        replacement = unicodedata.normalize("NFKC", character)
        output.append(replacement)
        if replacement != character:
            changes.append(
                DeobfuscationChange(
                    index=index,
                    category="unicode_normalization",
                    original=character,
                    replacement=replacement,
                    confidence=0.99,
                    explanation="Standardized a Unicode compatibility character.",
                )
            )
    return "".join(output), changes


def _replace_homoglyphs(text: str) -> tuple[str, list[DeobfuscationChange]]:
    output: list[str] = []
    changes: list[DeobfuscationChange] = []
    for index, character in enumerate(text):
        originals = HOMOGLYPH_REVERSE_MAP.get(character)
        replacement = originals[0] if originals else character
        output.append(replacement)
        if originals:
            confidence = 0.98 if len(originals) == 1 else 0.80
            changes.append(
                DeobfuscationChange(
                    index=index,
                    category="homoglyph",
                    original=character,
                    replacement=replacement,
                    confidence=confidence,
                    explanation="Replaced a known Unicode lookalike with its Latin counterpart.",
                )
            )
    return "".join(output), changes


def _leet_eligible_indices(text: str, level: DecodeLevel) -> set[int]:
    """Find leetspeak markers occurring in word-like, rather than numeric, spans."""
    eligible: set[int] = set()
    index = 0
    while index < len(text):
        if not (text[index].isalnum() or text[index] in LEETSPEAK_REVERSE_MAP):
            index += 1
            continue

        end = index
        while end < len(text) and (
            text[end].isalnum() or text[end] in LEETSPEAK_REVERSE_MAP
        ):
            end += 1

        span = text[index:end]
        has_letter = any(character.isalpha() for character in span)
        if has_letter or level == "aggressive":
            eligible.update(
                position
                for position in range(index, end)
                if text[position] in LEETSPEAK_REVERSE_MAP
            )
        index = end
    return eligible


def _leet_options(text: str, index: int) -> tuple[str, ...]:
    character = text[index]
    options = list(LEETSPEAK_REVERSE_MAP[character])

    # "$" can represent "s", but the spacing transform can also inject it.
    if (
        character == "$"
        and index > 0
        and index + 1 < len(text)
        and text[index - 1].isalnum()
        and text[index + 1].isalnum()
    ):
        options.append("")
    return tuple(dict.fromkeys(options))


def _replace_leetspeak(
    text: str,
    level: DecodeLevel,
    max_candidates: int,
) -> tuple[list[str], list[DeobfuscationChange], bool]:
    eligible = _leet_eligible_indices(text, level)
    candidates = [""]
    changes: list[DeobfuscationChange] = []
    has_ambiguity = False

    for index, character in enumerate(text):
        if index not in eligible:
            candidates = [candidate + character for candidate in candidates]
            continue

        options = _leet_options(text, index)
        has_ambiguity = has_ambiguity or len(options) > 1
        expanded: list[str] = []
        for candidate in candidates:
            for option in options:
                value = candidate + option
                if value not in expanded:
                    expanded.append(value)
                if len(expanded) >= max_candidates:
                    break
            if len(expanded) >= max_candidates:
                break
        candidates = expanded

        replacement = options[0]
        changes.append(
            DeobfuscationChange(
                index=index,
                category="leetspeak",
                original=character,
                replacement=replacement,
                confidence=0.58 if len(options) > 1 else 0.84,
                explanation=(
                    "Selected the first of multiple plausible leetspeak readings."
                    if len(options) > 1
                    else "Reversed a leetspeak character inside a word-like span."
                ),
            )
        )

    return candidates, changes, has_ambiguity


def _collapse_repeated_whitespace(
    text: str,
    changes: list[DeobfuscationChange] | None,
) -> str:
    def replace(match: re.Match[str]) -> str:
        original = match.group(0)
        if changes is not None:
            changes.append(
                DeobfuscationChange(
                    index=match.start(),
                    category="spacing",
                    original=original,
                    replacement=" ",
                    confidence=0.96,
                    explanation="Collapsed a run of repeated whitespace.",
                )
            )
        return " "

    return re.sub(r"\s{2,}", replace, text)


def _join_spaced_character_runs(
    text: str,
    level: DecodeLevel,
    changes: list[DeobfuscationChange] | None,
) -> str:
    minimum_characters = 4 if level == "conservative" else 3
    repeated = minimum_characters - 1
    pattern = re.compile(
        rf"(?<!\w)(?:[^\W_]\s+){{{repeated},}}[^\W_](?!\w)",
        flags=re.UNICODE,
    )

    def replace(match: re.Match[str]) -> str:
        original = match.group(0)
        replacement = re.sub(r"\s+", "", original)
        if changes is not None:
            changes.append(
                DeobfuscationChange(
                    index=match.start(),
                    category="spacing",
                    original=original,
                    replacement=replacement,
                    confidence=0.78 if level == "conservative" else 0.64,
                    explanation="Joined a suspicious run of individually spaced characters.",
                )
            )
        return replacement

    return pattern.sub(replace, text)


def _remove_inline_noise(
    text: str,
    level: DecodeLevel,
    changes: list[DeobfuscationChange] | None,
) -> str:
    output: list[str] = []
    index = 0

    while index < len(text):
        if not (text[index].isalnum() or text[index] in _NOISE_SET):
            output.append(text[index])
            index += 1
            continue

        end = index
        while end < len(text) and (text[end].isalnum() or text[end] in _NOISE_SET):
            end += 1
        span = text[index:end]
        inline_noise = [
            offset
            for offset, character in enumerate(span)
            if (
                character in _NOISE_SET
                and offset > 0
                and offset + 1 < len(span)
                and span[offset - 1].isalnum()
                and span[offset + 1].isalnum()
            )
        ]
        density = len(inline_noise) / len(span) if span else 0.0
        should_remove = (
            bool(inline_noise)
            if level == "aggressive"
            else len(inline_noise) >= 2 and density >= 0.20
        )

        if not should_remove:
            output.append(span)
            index = end
            continue

        removable = set(inline_noise)
        for offset, character in enumerate(span):
            if offset not in removable:
                output.append(character)
                continue
            if changes is not None:
                changes.append(
                    DeobfuscationChange(
                        index=index + offset,
                        category="punctuation_noise",
                        original=character,
                        replacement="",
                        confidence=0.72 if level == "conservative" else 0.55,
                        explanation="Removed punctuation occurring inside a suspicious character run.",
                    )
                )
        index = end

    return "".join(output)


def _clean_spacing_and_noise(
    text: str,
    level: DecodeLevel,
    changes: list[DeobfuscationChange] | None = None,
) -> str:
    cleaned = _collapse_repeated_whitespace(text, changes)
    cleaned = _join_spaced_character_runs(cleaned, level, changes)
    return _remove_inline_noise(cleaned, level, changes)


def deobfuscate_text(
    text: str,
    *,
    level: DecodeLevel = "conservative",
    max_candidates: int = 5,
) -> DeobfuscationResult:
    """Recover and rank a small set of auditable, best-effort text candidates."""
    if level not in ("conservative", "aggressive"):
        raise ValueError("level must be 'conservative' or 'aggressive'.")
    if max_candidates < 1:
        raise ValueError("max_candidates must be at least 1.")

    input_analysis = suspicion_score(text)
    visible_text, invisible_changes = _remove_invisible_spacing(text)
    normalized, normalization_changes = _unicode_normalize(visible_text)
    spacing_changes: list[DeobfuscationChange] = []
    spacing_cleaned = _clean_spacing_and_noise(normalized, level, spacing_changes)
    deconfused, homoglyph_changes = _replace_homoglyphs(spacing_cleaned)
    leet_candidates, leet_changes, has_ambiguity = _replace_leetspeak(
        deconfused,
        level,
        max_candidates,
    )

    candidates: list[str] = []
    for candidate in leet_candidates:
        if candidate not in candidates:
            candidates.append(candidate)
    candidates.sort(key=lambda candidate: suspicion_score(candidate).score)
    candidates = candidates[:max_candidates]

    best_candidate = candidates[0]
    if leet_candidates[0] != best_candidate:
        # Candidate ranking can select another ambiguous reading; its structural
        # cleanup is still the same, but the leetspeak audit must acknowledge it.
        has_ambiguity = True

    changes = (
        invisible_changes
        + normalization_changes
        + spacing_changes
        + homoglyph_changes
        + leet_changes
    )
    residual_analysis = suspicion_score(best_candidate)
    confidences = [change.confidence for change in changes]
    recovery_confidence = sum(confidences) / len(confidences) if confidences else 1.0
    if has_ambiguity:
        recovery_confidence -= 0.10
    if level == "aggressive" and changes:
        recovery_confidence -= 0.08
    recovery_confidence = max(0.0, min(1.0, recovery_confidence))

    if input_analysis.score:
        suspicion_reduction = max(
            0.0,
            (input_analysis.score - residual_analysis.score) / input_analysis.score,
        )
    else:
        suspicion_reduction = 0.0

    unresolved_markers = residual_analysis.confusable_count + residual_analysis.invisible_count + len(
        _leet_eligible_indices(best_candidate, level)
    )
    warnings = [
        "Random insertions, deletions, and swaps cannot be reconstructed reliably."
    ]
    if has_ambiguity:
        warnings.append("One or more characters have multiple plausible readings.")
    if unresolved_markers:
        warnings.append(f"{unresolved_markers} known suspicious marker(s) remain unresolved.")
    if level == "aggressive":
        warnings.append("Aggressive cleanup may remove meaningful punctuation or spacing.")

    return DeobfuscationResult(
        original_text=text,
        best_candidate=best_candidate,
        alternatives=[candidate for candidate in candidates if candidate != best_candidate],
        changes=changes,
        input_suspicion_score=input_analysis.score,
        residual_suspicion_score=residual_analysis.score,
        recovery_confidence=recovery_confidence * 100.0,
        suspicion_reduction=suspicion_reduction * 100.0,
        unresolved_markers=unresolved_markers,
        warnings=warnings,
    )
