import unittest

from adversarial.transformations import (
    homoglyph_substitution,
    leetspeak_transformation,
    random_character_noise,
    spacing_punctuation_noise,
)


class TransformationTests(unittest.TestCase):
    def test_homoglyph_substitution_changes_text_with_high_probability(self):
        text = "paypal account"
        result = homoglyph_substitution(text, probability=1.0)
        self.assertNotEqual(result, text)

    def test_leetspeak_transformation_changes_text_with_high_probability(self):
        text = "click here to reset password"
        result = leetspeak_transformation(text, probability=1.0)
        self.assertNotEqual(result, text)

    def test_spacing_punctuation_noise_adds_extra_characters(self):
        text = "verify account now"
        result = spacing_punctuation_noise(text, probability=0.8)
        self.assertGreaterEqual(len(result), len(text))

    def test_random_character_noise_runs_without_errors(self):
        text = "example"
        result = random_character_noise(text, probability=0.5)
        self.assertIsInstance(result, str)

    def test_homoglyph_substitution_includes_lowercase_t(self):
        text = "test"
        result = homoglyph_substitution(text, probability=1.0)
        self.assertNotEqual(result, text)
        self.assertTrue(any(ch in ("τ", "т") for ch in result))


if __name__ == "__main__":
    unittest.main()
