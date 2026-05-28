"""Shared diagnostic event logging (UI, file, terminal)."""
from __future__ import annotations

import sys
from datetime import datetime
from typing import Callable, Optional

EventCallback = Callable[[str, str, Optional[str]], None]


def format_event(level: str, message: str, detail: Optional[str] = None) -> str:
    """Format a diagnostic event into a timestamped log line."""
    ts = datetime.now().strftime("%H:%M:%S")
    level = (level or "INFO").upper()
    line = f"[{ts}] [{level}] {message}"
    if detail:
        line += f" — {detail}"
    return line


def print_event(level: str, message: str, detail: Optional[str] = None) -> None:
    """Write one line to stderr so it appears in the terminal when running python main.py."""
    try:
        print(format_event(level, message, detail), file=sys.stderr, flush=True)
    except Exception:
        pass
