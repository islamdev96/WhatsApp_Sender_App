"""WhatsApp Sender Pro — Offline License Activation System.

Generates a hardware-bound HWID and validates cryptographic license keys locally.
"""
import subprocess
import hashlib
import os
import getpass
import platform


SALT = "WHATSAPP_TURBO_PRO_SECRET_SALT_2026"
KEY_FILE = "activation.key"


def get_hwid() -> str:
    """Generates a stable, unique Hardware Identification string for the computer."""
    try:
        # Get machine UUID via WMIC on Windows
        uuid_out = subprocess.check_output("wmic csproduct get uuid", shell=True).decode().split("\n")[1].strip()
        if not uuid_out or "uuid" in uuid_out.lower():
            raise ValueError("Invalid UUID returned")
    except Exception:
        # Robust fallback using platform node, processor, and username
        try:
            uuid_out = f"{platform.node()}-{platform.processor()}-{getpass.getuser()}"
        except Exception:
            uuid_out = "OFFLINE-DESKTOP-LICENSE-HWID-KEY"

    hashed = hashlib.sha256(uuid_out.encode("utf-8")).hexdigest().upper()
    return f"{hashed[:4]}-{hashed[4:8]}-{hashed[8:12]}-{hashed[12:16]}"


def generate_license_key(hwid: str) -> str:
    """Cryptographically signs the HWID with a secret salt to generate the activation key."""
    clean_hwid = str(hwid).strip()
    raw_str = f"{clean_hwid}-{SALT}"
    hashed = hashlib.sha256(raw_str.encode("utf-8")).hexdigest().upper()
    return f"WSP-{hashed[:4]}-{hashed[4:8]}-{hashed[8:12]}-{hashed[12:16]}"


def verify_stored_license() -> bool:
    """Checks if the local activation.key file contains a valid activation key for this HWID."""
    if not os.path.exists(KEY_FILE):
        return False
    try:
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            stored_key = f.read().strip()
        hwid = get_hwid()
        expected = generate_license_key(hwid)
        return stored_key == expected
    except Exception:
        return False


def save_license_key(key: str) -> bool:
    """Validates and saves the license key locally if it matches this machine's HWID."""
    key = str(key).strip()
    hwid = get_hwid()
    expected = generate_license_key(hwid)
    if key == expected:
        try:
            with open(KEY_FILE, "w", encoding="utf-8") as f:
                f.write(key)
            return True
        except Exception:
            return False
    return False
