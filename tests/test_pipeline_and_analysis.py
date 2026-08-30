import unittest

from analysis.scoring import (
    detect_confusables,
    detect_invisible_spacing,
    suspicion_score,
    unicode_normalize,
)
from pipeline.generator import PipelineConfig, apply_pipeline, generate_variants, resolve_transforms


class PipelineAnalysisTests(unittest.TestCase):
    def test_pipeline_generates_requested_number_of_variants(self):
        variants = generate_variants("your account was suspended", num_variants=4, seed=42)
        self.assertEqual(len(variants), 4)

    def test_normalization_handles_unicode(self):
        text = "ｅxample"
        normalized = unicode_normalize(text)
        self.assertEqual(normalized, "example")

    def test_confusable_detection_counts_expected_chars(self):
        text = "pаypаl"  # includes cyrillic a characters
        count = detect_confusables(text)
        self.assertGreaterEqual(count, 1)

    def test_suspicion_score_returns_expected_fields(self):
        result = suspicion_score("cl!ck h3re n0w")
        self.assertGreaterEqual(result.score, 0)
        self.assertTrue(result.normalized_text)

    def test_pipeline_config_is_respected(self):
        config = PipelineConfig(
            homoglyph_probability=0.0,
            leetspeak_probability=0.0,
            spacing_noise_probability=0.0,
            invisible_spacing_probability=0.0,
            random_noise_probability=0.0,
        )
        variants = generate_variants("safe text", num_variants=1, config=config, seed=7)
        self.assertEqual(variants[0], "safe text")

    def test_resolve_transforms_supports_only_and_exclude(self):
        resolved = resolve_transforms(
            only=["homoglyph", "spacing_punctuation_noise"],
            exclude=["homoglyph_substitution"],
        )
        self.assertEqual(resolved, ["spacing_noise"])

    def test_apply_pipeline_respects_transform_subset(self):
        config = PipelineConfig(
            homoglyph_probability=1.0,
            leetspeak_probability=1.0,
            spacing_noise_probability=0.0,
            invisible_spacing_probability=0.0,
            random_noise_probability=0.0,
        )
        text = "a"
        only_leet = apply_pipeline(text=text, config=config, seed=5, transforms=["leetspeak"])
        only_homoglyph = apply_pipeline(text=text, config=config, seed=5, transforms=["homoglyph"])
        self.assertEqual(only_leet, "4")
        self.assertNotEqual(only_homoglyph, "4")

    def test_generate_variants_respects_exclude_transforms(self):
        config = PipelineConfig(
            homoglyph_probability=1.0,
            leetspeak_probability=1.0,
            spacing_noise_probability=0.0,
            invisible_spacing_probability=0.0,
            random_noise_probability=0.0,
        )
        variants = generate_variants(
            text="a",
            num_variants=1,
            config=config,
            seed=2,
            exclude_transforms=["homoglyph"],
        )
        self.assertEqual(variants[0], "4")

    def test_invisible_spacing_is_detected_and_scored(self):
        text = "pay\u200bpal"
        result = suspicion_score(text)
        self.assertEqual(detect_invisible_spacing(text), 1)
        self.assertEqual(result.invisible_count, 1)
        self.assertGreater(result.score, 0)


if __name__ == "__main__":
    unittest.main()
