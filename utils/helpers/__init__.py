"""
Helpers package — backward-compatible re-exports.
All existing `from utils.helpers import X` statements continue to work.
"""
from utils.helpers.phone import normalize_phone, _normalize_phone
from utils.helpers.contacts_io import (
    read_contacts,
    read_contacts_excel,
    read_contacts_txt,
    read_contacts_auto,
    create_contacts_template,
)
from utils.helpers.proxy import check_proxy, create_proxy_extension, cleanup_proxy_extension
from utils.helpers.fingerprint import generate_random_fingerprint
from utils.helpers.cleanup import cleanup_old_reports
from utils.helpers.text import parse_spintax

__all__ = [
    "normalize_phone", "_normalize_phone",
    "read_contacts", "read_contacts_excel", "read_contacts_txt",
    "read_contacts_auto", "create_contacts_template",
    "check_proxy", "create_proxy_extension", "cleanup_proxy_extension",
    "generate_random_fingerprint", "cleanup_old_reports",
    "parse_spintax",
]
