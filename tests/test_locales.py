"""
Unit tests for the Internationalization (i18n) locales structure.
Ensures Arabic and English translations are perfectly synchronized.
"""
import os
import sys
import json
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestLocalesConsistency(unittest.TestCase):
    """Verifies consistency between the en and ar translation catalogs."""

    def setUp(self):
        self.locale_file = os.path.join("data", "locales.json")
        self.assertTrue(os.path.exists(self.locale_file), "locales.json must exist in data directory")
        with open(self.locale_file, "r", encoding="utf-8") as f:
            self.locales = json.load(f)

    def test_top_level_languages(self):
        """Must have exactly 'en' and 'ar' keys at the top level."""
        self.assertIn("en", self.locales)
        self.assertIn("ar", self.locales)
        self.assertEqual(set(self.locales.keys()), {"en", "ar"})

    def test_matching_keys(self):
        """English and Arabic must have identical translation keys."""
        en_keys = set(self.locales["en"].keys())
        ar_keys = set(self.locales["ar"].keys())

        missing_in_ar = en_keys - ar_keys
        missing_in_en = ar_keys - en_keys

        self.assertEqual(
            missing_in_ar, set(),
            f"Keys found in EN but missing in AR: {missing_in_ar}"
        )
        self.assertEqual(
            missing_in_en, set(),
            f"Keys found in AR but missing in EN: {missing_in_en}"
        )

    def test_non_empty_values(self):
        """All translation values must be non-empty strings."""
        for lang in ["en", "ar"]:
            for key, val in self.locales[lang].items():
                self.assertTrue(
                    isinstance(val, str),
                    f"Translation value for {lang}.{key} must be a string"
                )
                self.assertTrue(
                    len(val.strip()) > 0,
                    f"Translation value for {lang}.{key} cannot be empty"
                )


if __name__ == "__main__":
    unittest.main()
