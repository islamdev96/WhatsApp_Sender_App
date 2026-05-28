"""
Tests for utils/event_log.py — event formatting.
"""
import unittest
from utils.event_log import format_event


class TestEventLog(unittest.TestCase):
    """Test format_event output."""

    def test_format_event_basic(self):
        """format_event returns a timestamped string with level and message."""
        result = format_event("INFO", "test message")
        self.assertIsInstance(result, str)
        self.assertIn("INFO", result)
        self.assertIn("test message", result)

    def test_format_event_with_detail(self):
        """format_event includes the detail when provided."""
        result = format_event("WARN", "login attempt", detail="timeout after 30s")
        self.assertIn("WARN", result)
        self.assertIn("login attempt", result)
        self.assertIn("timeout after 30s", result)

    def test_format_event_no_detail(self):
        """format_event works without detail argument."""
        result = format_event("DEBUG", "ping")
        self.assertIn("ping", result)
        self.assertNotIn("—", result)  # No detail separator


if __name__ == "__main__":
    unittest.main()
