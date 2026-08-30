import unittest

from adversarial_text import deobfuscate_text


class DeobfuscationTests(unittest.TestCase):
    def test_reverses_known_homoglyphs(self):
        result = deobfuscate_text("pаypаl")

        self.assertEqual(result.best_candidate, "paypal")
        self.assertEqual(
            sum(change.category == "homoglyph" for change in result.changes),
            2,
        )
        self.assertLess(result.residual_suspicion_score, result.input_suspicion_score)

    def test_reverses_leetspeak_in_word_like_spans_but_preserves_numbers(self):
        result = deobfuscate_text("h3ll0 2026")

        self.assertEqual(result.best_candidate, "hello 2026")
        self.assertNotIn("zozg", result.best_candidate)
        self.assertEqual(result.unresolved_markers, 0)

    def test_reports_ambiguous_leetspeak_alternatives(self):
        result = deobfuscate_text("m1lk", max_candidates=3)

        self.assertIn(result.best_candidate, {"milk", "mllk"})
        self.assertTrue(
            {"milk", "mllk"}.issubset({result.best_candidate, *result.alternatives})
        )
        self.assertTrue(any("multiple plausible" in warning for warning in result.warnings))

    def test_joins_suspicious_spaced_character_runs(self):
        result = deobfuscate_text("p a y p a l")

        self.assertEqual(result.best_candidate, "paypal")
        self.assertTrue(any(change.category == "spacing" for change in result.changes))

    def test_removes_dense_inline_punctuation_noise(self):
        result = deobfuscate_text("h.e_l-l!o")

        self.assertEqual(result.best_candidate, "hello")
        self.assertTrue(
            any(change.category == "punctuation_noise" for change in result.changes)
        )

    def test_removes_invisible_spacing_with_an_audit_entry(self):
        result = deobfuscate_text("pay\u200bpal\u2060")

        self.assertEqual(result.best_candidate, "paypal")
        self.assertEqual(
            sum(change.category == "invisible_spacing" for change in result.changes),
            2,
        )

    def test_aggressive_cleanup_can_make_leetspeak_word_like(self):
        result = deobfuscate_text("t 3 s t", level="aggressive")

        self.assertEqual(result.best_candidate, "test")

    def test_rejects_invalid_candidate_limit(self):
        with self.assertRaises(ValueError):
            deobfuscate_text("text", max_candidates=0)


if __name__ == "__main__":
    unittest.main()
