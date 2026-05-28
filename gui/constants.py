"""
GUI layer constants — replaces magic numbers/strings in UI code.
"""

# ── UI timing (milliseconds) ──
UI_QUEUE_POLL_MS = 50
STATUS_MONITOR_INTERVAL_MS = 3000
PROGRESS_UPDATE_INTERVAL_MS = 100

# ── Limits ──
MAX_CONTACT_PREVIEW = 50
REPORT_RETENTION_DAYS = 30

# ── Window ──
DEFAULT_WINDOW_WIDTH = 1000
DEFAULT_WINDOW_HEIGHT = 700
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 650

# ── File dialog filters ──
CONTACTS_FILE_TYPES = [
    ("All Supported", "*.csv *.xlsx *.txt"),
    ("CSV", "*.csv"),
    ("Excel", "*.xlsx"),
    ("Text", "*.txt"),
]

MEDIA_FILE_TYPES = [
    ("Images", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
    ("Videos", "*.mp4 *.avi *.mov *.mkv *.3gp *.webm"),
    ("Documents", "*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx"),
    ("All Files", "*.*"),
]
