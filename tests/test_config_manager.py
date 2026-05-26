import json
import logging
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config_manager import ConfigManager, DEFAULT_CONFIG
from utils.safety import MIN_BATCH_PAUSE_SECONDS, MIN_DELAY_SECONDS


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def _write_json(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _read_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_missing_config_uses_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.json")

            manager = ConfigManager(config_path=path)

            self.assertEqual(manager.get("language"), DEFAULT_CONFIG["language"])
            self.assertEqual(manager.get("delay_min"), DEFAULT_CONFIG["delay_min"])

    def test_invalid_json_keeps_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("{bad json")

            manager = ConfigManager(config_path=path)

            self.assertEqual(manager.get("language"), DEFAULT_CONFIG["language"])
            self.assertEqual(manager.get("delay_min"), DEFAULT_CONFIG["delay_min"])

    def test_non_object_json_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.json")
            self._write_json(path, ["bad"])

            manager = ConfigManager(config_path=path)

            self.assertEqual(manager.get("language"), DEFAULT_CONFIG["language"])
            self.assertEqual(manager.get("last_message"), DEFAULT_CONFIG["last_message"])

    def test_safe_limits_are_enforced_and_persisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.json")
            self._write_json(
                path,
                {
                    "delay_min": 1,
                    "delay_max": 2,
                    "batch_pause_min": 1,
                    "max_retries": 5,
                    "retry_full_navigation": True,
                },
            )

            manager = ConfigManager(config_path=path)
            saved = self._read_json(path)

            self.assertEqual(manager.get("delay_min"), MIN_DELAY_SECONDS)
            self.assertEqual(manager.get("delay_max"), float(MIN_DELAY_SECONDS) + 30)
            self.assertEqual(manager.get("batch_pause_min"), MIN_BATCH_PAUSE_SECONDS)
            self.assertEqual(manager.get("max_retries"), 1)
            self.assertFalse(manager.get("retry_full_navigation"))
            self.assertEqual(saved["delay_min"], MIN_DELAY_SECONDS)
            self.assertEqual(saved["batch_pause_min"], MIN_BATCH_PAUSE_SECONDS)
            self.assertFalse(saved["retry_full_navigation"])

    def test_invalid_numeric_safety_values_restore_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.json")
            self._write_json(
                path,
                {
                    "delay_min": "bad",
                    "delay_max": "bad",
                    "batch_pause_min": None,
                    "max_retries": [],
                },
            )

            manager = ConfigManager(config_path=path)
            saved = self._read_json(path)

            self.assertEqual(manager.get("delay_min"), DEFAULT_CONFIG["delay_min"])
            self.assertEqual(manager.get("delay_max"), DEFAULT_CONFIG["delay_max"])
            self.assertEqual(manager.get("batch_pause_min"), DEFAULT_CONFIG["batch_pause_min"])
            self.assertEqual(manager.get("max_retries"), DEFAULT_CONFIG["max_retries"])
            self.assertEqual(saved["delay_min"], DEFAULT_CONFIG["delay_min"])
            self.assertEqual(saved["max_retries"], DEFAULT_CONFIG["max_retries"])

    def test_set_and_save_persists_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.json")
            manager = ConfigManager(config_path=path)

            manager.set_and_save("last_message", "hello")

            reloaded = ConfigManager(config_path=path)
            self.assertEqual(reloaded.get("last_message"), "hello")


if __name__ == "__main__":
    unittest.main()
