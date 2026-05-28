"""
Automation layer constants — replaces magic numbers/strings scattered in the code.
"""

# ── WhatsApp Web ──
WHATSAPP_URL = "https://web.whatsapp.com"
WHATSAPP_PHONE_URL = "https://web.whatsapp.com/send/?phone={phone}&text&type=phone_number&app_absent=0"

# ── Timeouts (seconds) ──
LOGIN_TIMEOUT = 900
CHAT_LOAD_TIMEOUT = 60
MEDIA_PREVIEW_TIMEOUT = 12
CAPTION_BOX_TIMEOUT = 12
FOOTER_COMPOSE_TIMEOUT = 20
FILE_INPUT_WAIT = 8
PREVIEW_CLOSE_TIMEOUT = 5
CHAT_READY_AFTER_ATTACH_TIMEOUT = 15
INVALID_NUMBER_MODAL_TIMEOUT = 5

# ── Delays (seconds) ──
BROWSER_FLUSH_DELAY = 0.5
SCROLL_DELAY = (0.3, 0.8)
TYPING_CHAR_DELAY = (0.02, 0.08)
POST_SEND_DELAY = (0.5, 1.5)
INTER_ATTACHMENT_DELAY = (1.0, 2.0)

# ── Retry / scroll limits ──
MAX_SCROLL_ATTEMPTS = 5
MAX_SEND_RETRIES = 3
MAX_ATTACH_RETRIES = 3
MAX_FILE_INPUT_RETRIES = 3

# ── Selectors file ──
SELECTORS_FILENAME = "selectors.json"
