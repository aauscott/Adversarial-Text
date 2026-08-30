"""Composable transformation pipeline."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

from adversarial.transformations import (
    homoglyph_substitution,
    invisible_spacing_noise,
    leetspeak_transformation,
    random_character_noise,
    spacing_punctuation_noise,
)


@dataclass
class PipelineConfig:
    """Controls transformation probabilities in the pipeline."""

    homoglyph_probability: float = 0.2
    leetspeak_probability: float = 0.2
    spacing_noise_probability: float = 0.08
    invisible_spacing_probability: float = 0.02
    random_noise_probability: float = 0.04
    homoglyph_include_sets: tuple[str, ...] | None = None
    homoglyph_exclude_sets: tuple[str, ...] = ()
    preserve_digits: bool = False


DEFAULT_TRANSFORM_ORDER = [
    "homoglyph",
    "leetspeak",
    "spacing_noise",
    "invisible_spacing",
    "random_noise",
]
TRANSFORM_ALIASES = {
    "homoglyph": "homoglyph",
    "homoglyph_substitution": "homoglyph",
    "leet": "leetspeak",
    "leetspeak": "leetspeak",
    "leetspeak_transformation": "leetspeak",
    "spacing": "spacing_noise",
    "spacing_noise": "spacing_noise",
    "spacing_punctuation_noise": "spacing_noise",
    "invisible": "invisible_spacing",
    "invisible_spacing": "invisible_spacing",
    "invisible_spacing_noise": "invisible_spacing",
    "random": "random_noise",
    "random_noise": "random_noise",
    "random_character_noise": "random_noise",
}


def _canonicalize_transform_names(names: Sequence[str] | None) -> list[str]:
    if not names:
        return []

    canonical: list[str] = []
    unknown: list[str] = []
    for name in names:
        key = name.strip().lower()
        mapped = TRANSFORM_ALIASES.get(key)
        if mapped is None:
            unknown.append(name)
            continue
        if mapped not in canonical:
            canonical.append(mapped)

    if unknown:
        supported = ", ".join(DEFAULT_TRANSFORM_ORDER)
        unknown_str = ", ".join(unknown)
        raise ValueError(
            f"Unknown transform(s): {unknown_str}. Supported transforms: {supported}"
        )

    return canonical


def resolve_transforms(
    only: Sequence[str] | None = None,
    exclude: Sequence[str] | None = None,
) -> list[str]:
    """
    Resolve user transform choices into canonical pipeline order.
    """
    selected = (
        _canonicalize_transform_names(only) if only else list(DEFAULT_TRANSFORM_ORDER)
    )
    excluded = set(_canonicalize_transform_names(exclude))

    resolved = [name for name in selected if name not in excluded]
    if not resolved:
        raise ValueError("No transforms enabled after applying --only/--exclude.")
    return resolved


def apply_pipeline(
    text: str,
    config: PipelineConfig | None = None,
    seed: int | None = None,
    transforms: Sequence[str] | None = None,
) -> str:
    """Run all transformations in a fixed sequence."""
    active_config = config or PipelineConfig()
    rng = random.Random(seed)
    active_transforms = resolve_transforms(only=transforms)

    transformed = text
    for transform_name in active_transforms:
        if transform_name == "homoglyph":
            transformed = homoglyph_substitution(
                text=transformed,
                probability=active_config.homoglyph_probability,
                rng=rng,
                include_sets=active_config.homoglyph_include_sets,
                exclude_sets=active_config.homoglyph_exclude_sets,
                preserve_digits=active_config.preserve_digits,
            )
        elif transform_name == "leetspeak":
            transformed = leetspeak_transformation(
                text=transformed, probability=active_config.leetspeak_probability, rng=rng
            )
        elif transform_name == "spacing_noise":
            transformed = spacing_punctuation_noise(
                text=transformed, probability=active_config.spacing_noise_probability, rng=rng
            )
        elif transform_name == "invisible_spacing":
            transformed = invisible_spacing_noise(
                text=transformed,
                probability=active_config.invisible_spacing_probability,
                rng=rng,
            )
        elif transform_name == "random_noise":
            transformed = random_character_noise(
                text=transformed, probability=active_config.random_noise_probability, rng=rng
            )
    return transformed


def generate_variants(
    text: str,
    num_variants: int = 5,
    config: PipelineConfig | None = None,
    seed: int | None = None,
    transforms: Sequence[str] | None = None,
    exclude_transforms: Sequence[str] | None = None,
) -> list[str]:
    """Generate multiple adversarial variants from a single input."""
    resolved_transforms = resolve_transforms(only=transforms, exclude=exclude_transforms)
    root_rng = random.Random(seed)
    variants: list[str] = []
    for _ in range(num_variants):
        variant_seed = root_rng.randint(0, 2**32 - 1)
        variants.append(
            apply_pipeline(
                text=text,
                config=config,
                seed=variant_seed,
                transforms=resolved_transforms,
            )
        )
    return variants
