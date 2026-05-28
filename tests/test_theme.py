"""
Tests for gui/theme.py — palette and font consistency.
"""
import unittest
from gui.theme import PALETTE_DARK, PALETTE_LIGHT, FONTS


class TestTheme(unittest.TestCase):
    """Verify theme constants are well-formed."""

    def test_palettes_have_same_keys(self):
        """Dark and light palettes must define the same color keys."""
        self.assertEqual(set(PALETTE_DARK.keys()), set(PALETTE_LIGHT.keys()))

    def test_all_colors_are_hex(self):
        """All palette values must be valid hex color strings."""
        import re
        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        for name, palette in [("dark", PALETTE_DARK), ("light", PALETTE_LIGHT)]:
            for key, value in palette.items():
                self.assertTrue(
                    hex_pattern.match(value),
                    f"{name}.{key} = '{value}' is not a valid hex color",
                )

    def test_fonts_are_tuples(self):
        """All font definitions must be tuples of (family, size[, weight])."""
        for key, font in FONTS.items():
            self.assertIsInstance(font, tuple, f"FONTS['{key}'] should be a tuple")
            self.assertGreaterEqual(len(font), 2, f"FONTS['{key}'] needs at least (family, size)")
            self.assertIsInstance(font[0], str)
            self.assertIsInstance(font[1], int)

    def test_required_palette_keys(self):
        """Palettes must contain essential UI color keys."""
        required = {"primary", "danger", "success", "warning", "card_bg", "bg_dark",
                     "text_main", "text_muted", "border"}
        for key in required:
            self.assertIn(key, PALETTE_DARK, f"Missing '{key}' in PALETTE_DARK")
            self.assertIn(key, PALETTE_LIGHT, f"Missing '{key}' in PALETTE_LIGHT")


if __name__ == "__main__":
    unittest.main()
