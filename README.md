# WhatsApp Sender Pro

Desktop bulk messaging for **WhatsApp Web** (Selenium automation). Not affiliated with Meta/WhatsApp.

## Quick start

1. Install Python 3.11+ and Google Chrome.
2. `pip install -r requirements.txt`
3. `python main.py`
4. Click **فتح WhatsApp** and scan the QR code once per profile.
5. Add contacts, message, optional attachments → **إرسال الآن**.

## Recommended settings (stability)

| Setting | Recommendation |
|--------|----------------|
| إرسال النص كوصف (وضع مدمج) | **Off** — sends image first, then text as a separate message |
| الوضع الآمن عند البدء | **On** — validates numbers before sending |
| التأخير بين الرسائل | 30–120 seconds for large lists |
| إعادة المحاولة | 1 (default) |
| وضع الخلفية | On for long campaigns |

## Features

- Bulk send with `{name}`, `{phone}`, `{var1}`–`{var5}`, Spintax `{a|b|c}`
- Multi-attachment (image / video / document) with per-file captions
- Contact groups, templates, workflows (multi-step sequences)
- Campaign history + CSV reports (`reports/`)
- Number checker, Google Maps scraper, account warmer
- Keyword auto-reply (main tab) + chatbot tab
- Multi Chrome profiles, proxy, fingerprint options

## Limits (important)

- Uses **WhatsApp Web automation** — UI changes can break selectors; update `automation/selectors.json` if needed.
- No official WhatsApp Business API — higher ban risk than approved business tools.
- "Success" means the bot completed UI steps, not delivery/read receipts.

## Build executable

See `README_INSTALL.txt` and `python build.py` for PyInstaller output in `dist/`.

## Project layout

- `main.py` — entry point
- `gui/modern_ui.py` — application UI
- `automation/whatsapp_bot.py` — Selenium bot
- `utils/` — config, database, campaigns, contacts
- `data/` — SQLite DB, profiles, auto-reply rules
