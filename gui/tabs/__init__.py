"""WhatsApp Sender Pro — Modular GUI tabs."""
from gui.tabs.main_tab import build_main_tab
from gui.tabs.groups_tab import build_groups_tab
from gui.tabs.templates_tab import build_templates_tab
from gui.tabs.settings_tab import build_settings_tab
from gui.tabs.log_tab import build_log_tab

__all__ = [
    "build_main_tab",
    "build_groups_tab",
    "build_templates_tab",
    "build_settings_tab",
    "build_log_tab",
]
