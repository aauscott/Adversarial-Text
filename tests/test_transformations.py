import unittest

from adversarial_text import (
    HOMOGLYPH_MAP,
    INVISIBLE_SPACING_CHARS,
    homoglyph_substitution,
    invisible_spacing_noise,
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
        result = homoglyph_substitution(
            text,
            probability=1.0,
            include_sets=("greek", "cyrillic"),
        )
        self.assertNotEqual(result, text)
        self.assertTrue(any(ch in ("τ", "т") for ch in result))

    def test_expanded_map_covers_ascii_letters_and_digits(self):
        for character in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
            self.assertIn(character, HOMOGLYPH_MAP)
            self.assertTrue(HOMOGLYPH_MAP[character])

    def test_information_symbol_is_an_intentional_i_replacement(self):
        self.assertIn("ℹ", HOMOGLYPH_MAP["i"])

    def test_homoglyph_sets_can_be_included_or_excluded(self):
        cyrillic = homoglyph_substitution(
            "a", probability=1.0, include_sets=("cyrillic",)
        )
        greek = homoglyph_substitution(
            "a",
            probability=1.0,
            include_sets=("greek",),
            exclude_sets=("cyrillic",),
        )
        self.assertEqual(cyrillic, "а")
        self.assertEqual(greek, "α")

    def test_homoglyph_substitution_rejects_unknown_set(self):
        with self.assertRaises(ValueError):
            homoglyph_substitution("text", include_sets=("unknown",))

    def test_homoglyph_substitution_can_preserve_digits(self):
        result = homoglyph_substitution(
            "a123",
            probability=1.0,
            include_sets=("fullwidth",),
            preserve_digits=True,
        )
        self.assertEqual(result, "ａ123")

    def test_invisible_spacing_noise_inserts_known_characters(self):
        text = "test"
        result = invisible_spacing_noise(text, probability=1.0)
        inserted = [character for character in result if character in INVISIBLE_SPACING_CHARS]
        self.assertEqual(len(inserted), len(text))


if __name__ == "__main__":
    unittest.main()
