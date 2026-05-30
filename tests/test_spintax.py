"""Unit tests for anti-ban Spintax parsing helper."""
import unittest
from utils.helpers.text import parse_spintax


class TestSpintax(unittest.TestCase):
    def test_basic_spintax(self):
        """Assert basic single-level spintax choices resolve correctly."""
        text = "{Hello|Hi|Hey} there"
        parsed = parse_spintax(text)
        self.assertIn(parsed, ["Hello there", "Hi there", "Hey there"])

    def test_nested_spintax(self):
        """Assert nested spintax expressions resolve successfully from inside-out."""
        text = "{Hello {friend|dear}|Hi}"
        parsed = parse_spintax(text)
        self.assertIn(parsed, ["Hello friend", "Hello dear", "Hi"])

    def test_no_spintax(self):
        """Assert normal text with no curly braces is returned unmodified."""
        text = "Hello simple text"
        self.assertEqual(parse_spintax(text), "Hello simple text")

    def test_empty_text(self):
        """Assert empty inputs return empty strings cleanly."""
        self.assertEqual(parse_spintax(""), "")
