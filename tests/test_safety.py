import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.safety import (
    assess_campaign_settings,
    extra_delay_after_attachment,
    normalize_media_type,
)


class TestSafety(unittest.TestCase):
    def test_normalize_video_extension(self):
        self.assertEqual(normalize_media_type("document", "clip.mp4"), "video")

    def test_extra_delay_video(self):
        self.assertGreater(extra_delay_after_attachment("video", "x.mp4"), 7.0)

    def test_assess_fast_campaign_not_ok(self):
        r = assess_campaign_settings(100, 5, 10, 30, 30, has_media=True)
        self.assertFalse(r["ok"])
        self.assertTrue(r["warnings"])


if __name__ == "__main__":
    unittest.main()
