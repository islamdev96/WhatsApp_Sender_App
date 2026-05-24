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
| وضع الخلفية | **Off** when sending images/video; On for text-only long campaigns |

## Media send flow (images / video)

1. Open chat → wait for footer (+) and message box.
2. Attach via menu (+) → **Photos & videos** → file injected (no Windows file picker).
3. Send preview → wait for preview to close.
4. Send text as a **separate message** (merged caption mode off).

## Common errors

| Code | Meaning | What to do |
|------|---------|------------|
| `ERR_ATTACH_BTN_NOT_FOUND` | Attach (+) not visible in footer | Keep WhatsApp window visible; close search/preview; retry |
| `ERR_TEXT_SEND` | Click blocked on text/send | Close media preview; disable background mode; bot auto-retries once |
| `INVALID` / نافذة «غير موجود على واتساب» | Number has no WhatsApp | Auto-clicks **موافق** and skips to next contact |
| `ERR_STICKER_PANEL_OPENED` | Wrong panel opened | Retry; do not click stickers manually during send |
| `ERR_FILE_INPUT_NOT_FOUND` | Upload field missing | Update `automation/selectors.json` if WhatsApp UI changed |

## Features

- Bulk send with `{name}`, `{phone}`, `{var1}`–`{var5}`, Spintax `{a|b|c}`
- Multi-attachment (image / video / document) with per-file captions
- Contact groups, templates, workflows (multi-step sequences)
- Campaign history + CSV reports (`reports/`)
- Number checker, Google Maps scraper, account warmer
- Keyword auto-reply (main tab) + chatbot tab
- Multi Chrome profiles, proxy, fingerprint options

## Anti-ban / policy (Arabic)

- استخدم **الوضع الآمن** واترك **وضع الدمج** (نص مع أول مرفق) **معطّلاً**.
- للصور والفيديو: تأخير **30–120 ثانية** بين الرسائل، واستراحة دفعة **60 ثانية** على الأقل.
- لا ترسل لقوائم ضخمة دفعة واحدة؛ قسّم الحملات (≤200 جهة/جلسة تقريباً).
- المحتوى يجب أن يكون مسموحاً بسياسة واتساب (لا سبام، لا محتوى محظور).
- **لا يوجد ضمان** بعدم الحظر — الأتمتة غير الرسمية مخالفة لشروط واتساب.

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
