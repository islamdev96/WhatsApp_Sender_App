"""WhatsApp Sender Pro — Modular GUI tabs."""
from gui.tabs.main_tab import build_main_tab
from gui.tabs.groups_tab import build_groups_tab
from gui.tabs.templates_tab import build_templates_tab
from gui.tabs.settings_tab import build_settings_tab
from gui.tabs.log_tab import build_log_tab
from gui.tabs.campaigns_tab import build_campaigns_tab
from gui.tabs.auto_reply_tab import build_auto_reply_tab
from gui.tabs.received_tab import build_received_tab
from gui.tabs.numbers_filter_tab import build_numbers_filter_tab
from gui.tabs.warmer_tab import build_warmer_tab
from gui.tabs.workflows_tab import build_workflows_tab
from gui.tabs.gmaps_tab import build_gmaps_tab

__all__ = [
    "build_main_tab",
    "build_groups_tab",
    "build_templates_tab",
    "build_settings_tab",
    "build_log_tab",
    "build_campaigns_tab",
    "build_auto_reply_tab",
    "build_received_tab",
    "build_numbers_filter_tab",
    "build_warmer_tab",
    "build_workflows_tab",
    "build_gmaps_tab",
]
