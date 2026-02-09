"""
Configuration Manager — Persistent settings for WhatsApp Sender Pro.
Saves and loads all user preferences to/from config.json.
"""
import json
import os

DEFAULT_CONFIG = {
    "appearance_mode": "dark",
    "language": "ar",
    "last_contacts_file": "",
    "last_image_file": "",
    "last_message": "",
    "send_text_with_image": True,
    "background_mode": False,
    "delay_min": 30,
    "delay_max": 120,
    "batch_size": 30,
    "batch_pause_min": 180,
    "batch_pause_max": 240,
    "max_retries": 2,
    "retry_delay_min": 3,
    "retry_delay_max": 6,
    "max_consecutive_failures": 5,
    "enable_spintax": True,
    "profile_name": "Default",
    "profiles_dir": os.path.join("data", "profiles"),
    "window_width": 1000,
    "window_height": 700,
}


class ConfigManager:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.getcwd(), "config.json")
        self.config_path = config_path
        self.config = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        """Load config from file, merging with defaults for any missing keys."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                self.config.update(saved)
        except Exception:
            pass

    def save(self):
        """Persist current config to disk."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

    def set_and_save(self, key, value):
        self.set(key, value)
        self.save()
