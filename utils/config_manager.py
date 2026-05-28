"""
Configuration Manager — Persistent settings for WhatsApp Sender Pro.
Saves and loads all user preferences to/from config.json.
"""
import json
import os
from utils.logger import logger, log_exception

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

    def load(self) -> None:
        """Load config from file, merging with defaults for any missing keys."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                if isinstance(saved, dict):
                    self.config.update(saved)
                else:
                    logger.warning("Ignoring config file because it does not contain an object: %s", self.config_path)
                    return
                # Prefer two-step send; merged caption mode is unreliable in automation.
                if self.config.get("send_text_with_image"):
                    self.config["send_text_with_image"] = False
                self._enforce_safe_limits(persist=True)
        except json.JSONDecodeError as exc:
            logger.error("Invalid config JSON in %s: %s", self.config_path, exc)
        except OSError as exc:
            logger.error("Could not read config file %s: %s", self.config_path, exc)
        except Exception as exc:
            log_exception(f"Unexpected error loading config from {self.config_path}", exc)

    def _enforce_safe_limits(self, persist=False):
        """Clamp aggressive settings that increase ban risk."""
        try:
            from utils.safety import MIN_DELAY_SECONDS, MIN_BATCH_PAUSE_SECONDS

            changed = False
            dmin, coerced = self._get_float_config("delay_min")
            changed = changed or coerced
            dmax, coerced = self._get_float_config("delay_max")
            changed = changed or coerced
            if dmin < MIN_DELAY_SECONDS:
                self.config["delay_min"] = MIN_DELAY_SECONDS
                changed = True
            if dmax < float(self.config["delay_min"]):
                self.config["delay_max"] = float(self.config["delay_min"]) + 30
                changed = True
            bpause, coerced = self._get_float_config("batch_pause_min")
            changed = changed or coerced
            if bpause < MIN_BATCH_PAUSE_SECONDS:
                self.config["batch_pause_min"] = MIN_BATCH_PAUSE_SECONDS
                changed = True
            max_retries, coerced = self._get_int_config("max_retries")
            changed = changed or coerced
            if max_retries > 2:
                self.config["max_retries"] = 1
                changed = True
            if self.config.get("retry_full_navigation"):
                self.config["retry_full_navigation"] = False
                changed = True
            if persist and changed:
                self.save()
        except (ValueError, TypeError) as exc:
            logger.warning("Invalid safety-related config values, keeping defaults where possible: %s", exc)
        except Exception as exc:
            log_exception("Error enforcing safe limits", exc)

    def _get_float_config(self, key):
        default = DEFAULT_CONFIG[key]
        try:
            return float(self.config.get(key, default)), False
        except (ValueError, TypeError):
            logger.warning("Invalid numeric config value for %s; restoring default %r", key, default)
            self.config[key] = default
            return float(default), True

    def _get_int_config(self, key):
        default = DEFAULT_CONFIG[key]
        try:
            return int(self.config.get(key, default)), False
        except (ValueError, TypeError):
            logger.warning("Invalid integer config value for %s; restoring default %r", key, default)
            self.config[key] = default
            return int(default), True

    def save(self) -> None:
        """Persist current config to disk."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            logger.error("Could not write config file %s: %s", self.config_path, exc)
        except Exception as exc:
            log_exception(f"Unexpected error saving config to {self.config_path}", exc)

    def get(self, key: str, default=None):
        return self.config.get(key, default)

    def set(self, key: str, value):
        # Stricter type enforcement and parsing for configuration values
        int_keys = {
            "batch_size", "max_retries", "max_consecutive_failures", 
            "window_width", "window_height"
        }
        float_keys = {
            "delay_min", "delay_max", "batch_pause_min", "batch_pause_max",
            "retry_delay_min", "retry_delay_max"
        }
        bool_keys = {
            "send_text_with_image", "background_mode", "retry_full_navigation",
            "enable_spintax", "auto_open_login", "use_valid_after_check", "use_workflow"
        }

        try:
            if key in int_keys and value is not None:
                value = int(float(value))
            elif key in float_keys and value is not None:
                value = float(value)
            elif key in bool_keys and value is not None:
                if isinstance(value, str):
                    value = value.lower() in ("true", "1", "yes")
                else:
                    value = bool(value)
        except (ValueError, TypeError) as exc:
            logger.warning("Type coercion failed for key '%s' with value '%r': %s", key, value, exc)
            # Revert to default/fallback instead of crashing or storing bad type
            from utils.config_manager import DEFAULT_CONFIG
            value = DEFAULT_CONFIG.get(key, value)

        self.config[key] = value

        # Automatically clamp safety settings on live updates
        safety_keys = {"delay_min", "delay_max", "batch_pause_min", "max_retries", "retry_full_navigation"}
        if key in safety_keys:
            self._enforce_safe_limits(persist=False)

    def set_and_save(self, key: str, value):
        self.set(key, value)
        self.save()
