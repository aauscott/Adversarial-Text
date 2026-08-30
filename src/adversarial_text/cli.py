"""Command-line interface for adversarial text generation and scoring."""

from __future__ import annotations

import argparse
import random

from .deobfuscation import DeobfuscationResult, deobfuscate_text
from .generator import DEFAULT_TRANSFORM_ORDER, PipelineConfig, apply_pipeline, resolve_transforms
from .homoglyph_data import HOMOGLYPH_SETS
from .scoring import suspicion_score


def _parse_transform_args(raw_values: list[str] | None) -> list[str] | None:
    if not raw_values:
        return None
    parsed: list[str] = []
    for raw in raw_values:
        parts = [segment.strip() for segment in raw.split(",")]
        parsed.extend([segment for segment in parts if segment])
    return parsed or None


def _parse_probability_spec(raw_value: str | None, flag_name: str) -> tuple[float, float] | None:
    """
    Parse probability input as either:
    - single value: "0.25"
    - range: "0.10:0.40"
    """
    if raw_value is None:
        return None

    value = raw_value.strip()
    if not value:
        raise ValueError(f"{flag_name} cannot be empty.")

    if ":" in value:
        parts = value.split(":")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(f"{flag_name} must be a float or min:max range.")
        low, high = float(parts[0]), float(parts[1])
    else:
        low = high = float(value)

    if low < 0.0 or high < 0.0 or low > 1.0 or high > 1.0:
        raise ValueError(f"{flag_name} must be within [0.0, 1.0].")
    if low > high:
        raise ValueError(f"{flag_name} range must satisfy min <= max.")
    return (low, high)


def _sample_probability(spec: tuple[float, float] | None, default: float, rng: random.Random) -> float:
    if spec is None:
        return default
    low, high = spec
    if low == high:
        return low
    return rng.uniform(low, high)


def _build_pipeline_config(
    rng: random.Random,
    global_spec: tuple[float, float] | None,
    homoglyph_spec: tuple[float, float] | None,
    leetspeak_spec: tuple[float, float] | None,
    spacing_spec: tuple[float, float] | None,
    random_spec: tuple[float, float] | None,
    invisible_spec: tuple[float, float] | None = None,
    homoglyph_include_sets: list[str] | None = None,
    homoglyph_exclude_sets: list[str] | None = None,
    preserve_digits: bool = False,
) -> PipelineConfig:
    defaults = PipelineConfig()
    return PipelineConfig(
        homoglyph_probability=_sample_probability(homoglyph_spec or global_spec, defaults.homoglyph_probability, rng),
        leetspeak_probability=_sample_probability(leetspeak_spec or global_spec, defaults.leetspeak_probability, rng),
        spacing_noise_probability=_sample_probability(spacing_spec or global_spec, defaults.spacing_noise_probability, rng),
        invisible_spacing_probability=_sample_probability(
            invisible_spec or global_spec,
            defaults.invisible_spacing_probability,
            rng,
        ),
        random_noise_probability=_sample_probability(random_spec or global_spec, defaults.random_noise_probability, rng),
        homoglyph_include_sets=(
            tuple(homoglyph_include_sets) if homoglyph_include_sets else None
        ),
        homoglyph_exclude_sets=tuple(homoglyph_exclude_sets or ()),
        preserve_digits=preserve_digits,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adversarial Text CLI")
    parser.add_argument("--text", required=True, help="Input text to transform or decode")
    parser.add_argument("--decode", action="store_true", help="Recover a best-effort clean reading of --text")
    parser.add_argument(
        "--decode-level",
        choices=("conservative", "aggressive"),
        default="conservative",
        help="How readily decoding may remove ambiguous punctuation or spacing (default: conservative)",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=5,
        help="Maximum decoded candidates to consider (default: 5)",
    )
    parser.add_argument("--variants", type=int, default=3, help="How many transformed variants to generate (default: 3)")
    parser.add_argument("--seed", type=int, default=None, help="Optional seed for reproducible output")
    parser.add_argument("--only", nargs="+", default=None, help=("Run only these transforms. Accepts space or comma separated names. " f"Canonical names: {', '.join(DEFAULT_TRANSFORM_ORDER)}"))
    parser.add_argument("--exclude", nargs="+", default=None, help=("Exclude these transforms from the selected set. Accepts space or comma separated names. " f"Canonical names: {', '.join(DEFAULT_TRANSFORM_ORDER)}"))
    parser.add_argument("--prob", default=None, help="Global probability as float or range min:max (e.g. 0.2 or 0.1:0.4).")
    parser.add_argument("--homoglyph-prob", default=None, help="Homoglyph probability as float or range min:max.")
    parser.add_argument("--leetspeak-prob", default=None, help="Leetspeak probability as float or range min:max.")
    parser.add_argument("--spacing-prob", default=None, help="Spacing noise probability as float or range min:max.")
    parser.add_argument("--invisible-prob", default=None, help="Invisible spacing probability as float or range min:max.")
    parser.add_argument("--random-prob", default=None, help="Random char noise probability as float or range min:max.")
    parser.add_argument(
        "--homoglyph-include",
        nargs="+",
        default=None,
        help=(
            "Use only these homoglyph sets (space or comma separated): "
            f"{', '.join(HOMOGLYPH_SETS)}"
        ),
    )
    parser.add_argument(
        "--homoglyph-exclude",
        nargs="+",
        default=None,
        help=(
            "Exclude these homoglyph sets (space or comma separated): "
            f"{', '.join(HOMOGLYPH_SETS)}"
        ),
    )
    parser.add_argument(
        "--preserve-digits",
        action="store_true",
        help="Do not replace existing digits during homoglyph substitution.",
    )
    return parser


def _print_decode_result(result: DeobfuscationResult) -> None:
    print(f"Input: {result.original_text}")
    print(f"Best candidate: {result.best_candidate}")
    print("")
    print(
        "Scores: input_suspicion={input_score:.2f}, residual_suspicion={residual_score:.2f}, "
        "recovery_confidence={confidence:.1f}%, suspicion_reduction={reduction:.1f}%".format(
            input_score=result.input_suspicion_score,
            residual_score=result.residual_suspicion_score,
            confidence=result.recovery_confidence,
            reduction=result.suspicion_reduction,
        )
    )
    print(f"Unresolved markers: {result.unresolved_markers}")

    print("")
    print("Changes:")
    if not result.changes:
        print("  None")
    for change in result.changes:
        original = repr(change.original)
        replacement = repr(change.replacement)
        print(
            f"  [{change.category}] index={change.index}: {original} -> {replacement} "
            f"(confidence={change.confidence * 100:.0f}%)"
        )
        print(f"    {change.explanation}")

    if result.alternatives:
        print("")
        print("Alternatives:")
        for index, alternative in enumerate(result.alternatives, start=1):
            print(f"  {index}. {alternative}")

    if result.warnings:
        print("")
        print("Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.decode:
        try:
            result = deobfuscate_text(
                args.text,
                level=args.decode_level,
                max_candidates=args.max_candidates,
            )
        except ValueError as exc:
            parser.error(str(exc))
        _print_decode_result(result)
        return

    only = _parse_transform_args(args.only)
    exclude = _parse_transform_args(args.exclude)
    homoglyph_include = _parse_transform_args(args.homoglyph_include)
    homoglyph_exclude = _parse_transform_args(args.homoglyph_exclude)

    try:
        active_transforms = resolve_transforms(only=only, exclude=exclude)

        global_spec = _parse_probability_spec(args.prob, "--prob")
        homoglyph_spec = _parse_probability_spec(args.homoglyph_prob, "--homoglyph-prob")
        leetspeak_spec = _parse_probability_spec(args.leetspeak_prob, "--leetspeak-prob")
        spacing_spec = _parse_probability_spec(args.spacing_prob, "--spacing-prob")
        invisible_spec = _parse_probability_spec(args.invisible_prob, "--invisible-prob")
        random_spec = _parse_probability_spec(args.random_prob, "--random-prob")

        root_rng = random.Random(args.seed)
        variants: list[str] = []
        for _ in range(args.variants):
            variant_seed = root_rng.randint(0, 2**32 - 1)
            config = _build_pipeline_config(
                rng=root_rng,
                global_spec=global_spec,
                homoglyph_spec=homoglyph_spec,
                leetspeak_spec=leetspeak_spec,
                spacing_spec=spacing_spec,
                random_spec=random_spec,
                invisible_spec=invisible_spec,
                homoglyph_include_sets=homoglyph_include,
                homoglyph_exclude_sets=homoglyph_exclude,
                preserve_digits=args.preserve_digits,
            )
            variants.append(
                apply_pipeline(text=args.text, config=config, seed=variant_seed, transforms=active_transforms)
            )
    except ValueError as exc:
        parser.error(str(exc))

    print(f"Input: {args.text}")
    print("")
    print("Generated variants:")

    for i, variant in enumerate(variants, start=1):
        result = suspicion_score(variant)
        print(f"{i}. {variant}")
        print(
            "   score={score:.2f}, confusables={confusables}, invisibles={invisibles}, "
            "leetspeak={leet}, punctuation_ratio={ratio:.3f}".format(
                score=result.score,
                confusables=result.confusable_count,
                invisibles=result.invisible_count,
                leet=result.leetspeak_count,
                ratio=result.punctuation_ratio,
            )
        )


if __name__ == "__main__":
    main()
