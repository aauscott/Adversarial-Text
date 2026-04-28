import random
import unittest

from cli import _build_pipeline_config, _parse_probability_spec


class CliProbabilityTests(unittest.TestCase):
    def test_parse_probability_spec_single_value(self):
        self.assertEqual(_parse_probability_spec("0.25", "--prob"), (0.25, 0.25))

    def test_parse_probability_spec_range(self):
        self.assertEqual(_parse_probability_spec("0.1:0.4", "--prob"), (0.1, 0.4))

    def test_parse_probability_spec_rejects_invalid_range_order(self):
        with self.assertRaises(ValueError):
            _parse_probability_spec("0.8:0.3", "--prob")

    def test_parse_probability_spec_rejects_out_of_bounds(self):
        with self.assertRaises(ValueError):
            _parse_probability_spec("1.1", "--prob")

    def test_build_pipeline_config_uses_global_and_specific_overrides(self):
        rng = random.Random(7)
        config = _build_pipeline_config(
            rng=rng,
            global_spec=(0.2, 0.2),
            homoglyph_spec=(0.7, 0.7),
            leetspeak_spec=None,
            spacing_spec=None,
            random_spec=None,
        )
        self.assertEqual(config.homoglyph_probability, 0.7)
        self.assertEqual(config.leetspeak_probability, 0.2)
        self.assertEqual(config.spacing_noise_probability, 0.2)
        self.assertEqual(config.random_noise_probability, 0.2)

    def test_build_pipeline_config_samples_ranges(self):
        rng = random.Random(11)
        config = _build_pipeline_config(
            rng=rng,
            global_spec=(0.1, 0.3),
            homoglyph_spec=None,
            leetspeak_spec=None,
            spacing_spec=None,
            random_spec=None,
        )
        self.assertGreaterEqual(config.homoglyph_probability, 0.1)
        self.assertLessEqual(config.homoglyph_probability, 0.3)


if __name__ == "__main__":
    unittest.main()
