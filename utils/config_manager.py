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
    "last_attachments": [],
    "last_message": "",
    "send_text_with_image": False,
    "background_mode": False,
    "delay_min": 30,
    "delay_max": 120,
    "batch_size": 30,
    "batch_pause_min": 180,
    "batch_pause_max": 240,
    "max_retries": 1,
    "retry_delay_min": 3,
    "retry_delay_max": 6,
    "retry_full_navigation": False,
    "max_consecutive_failures": 5,
    "enable_spintax": True,
    "auto_open_login": True,
    "use_valid_after_check": False,
    "use_workflow": False,
    "last_workflow": "",
    "profile_name": "Default",
    "profiles_dir": os.path.join("data", "profiles"),
    "window_width": 1000,
    "window_height": 700,
    "default_country_code": "20",
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
                # Prefer two-step send; merged caption mode is unreliable in automation.
                if self.config.get("send_text_with_image"):
                    self.config["send_text_with_image"] = False
                self._enforce_safe_limits(persist=True)
        except Exception:
            pass

    def _enforce_safe_limits(self, persist=False):
        """Clamp aggressive settings that increase ban risk."""
        try:
            from utils.safety import MIN_DELAY_SECONDS, MIN_BATCH_PAUSE_SECONDS

            changed = False
            dmin = float(self.config.get("delay_min", 30))
            dmax = float(self.config.get("delay_max", 120))
            if dmin < MIN_DELAY_SECONDS:
                self.config["delay_min"] = MIN_DELAY_SECONDS
                changed = True
            if dmax < float(self.config["delay_min"]):
                self.config["delay_max"] = float(self.config["delay_min"]) + 30
                changed = True
            bpause = float(self.config.get("batch_pause_min", 180))
            if bpause < MIN_BATCH_PAUSE_SECONDS:
                self.config["batch_pause_min"] = MIN_BATCH_PAUSE_SECONDS
                changed = True
            if int(self.config.get("max_retries", 1)) > 2:
                self.config["max_retries"] = 1
                changed = True
            if self.config.get("retry_full_navigation"):
                self.config["retry_full_navigation"] = False
                changed = True
            if persist and changed:
                self.save()
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
