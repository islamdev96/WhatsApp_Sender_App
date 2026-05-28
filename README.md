# WhatsApp Sender Pro

Professional WhatsApp messaging automation built with CustomTkinter and Selenium.

## Project Structure

```
WhatsApp_Sender_App/
├── main.py                     # Entry point
├── requirements.txt            # Dependencies (pinned)
├── run_app.bat                 # Quick launch script
│
├── automation/                 # Selenium automation layer
│   ├── bot.py                  # WhatsAppBot main class
│   ├── browser_setup.py        # Chrome driver setup & login
│   ├── chat_navigation.py      # Chat search & number validation
│   ├── messaging.py            # Text sending & clipboard
│   ├── media_handler.py        # File inputs & attachment previews
│   ├── chatbot.py              # Auto-reply (unread chats)
│   ├── constants.py            # Timeouts & retry limits
│   ├── gmaps_scraper.py        # Google Maps phone scraper
│   ├── whatsapp_navigator.py   # WhatsApp Web DOM navigation
│   └── selectors.json          # CSS/XPath selectors config
│
├── gui/                        # CustomTkinter UI layer
│   ├── app.py                  # ModernWhatsAppApp main window
│   ├── theme.py                # Colors, fonts, error catalog
│   ├── constants.py            # UI timing & limits
│   ├── components.py           # RichTextFrame, AttachmentManager
│   └── mixins/                 # UI logic split by concern
│       ├── tab_builders.py     # Tab construction & CRUD
│       ├── automation_mixin.py # Send/stop/pause control
│       ├── contacts_mixin.py   # Contact loading & spintax
│       ├── reporting_mixin.py  # Reports & CSV export
│       ├── dialogs_mixin.py    # Import & generator dialogs
│       └── progress_mixin.py   # Progress window
│
├── utils/                      # Shared utilities
│   ├── config_manager.py       # Settings persistence
│   ├── campaign_manager.py     # Campaign history (SQLite)
│   ├── contacts_manager.py     # Contact groups (SQLite)
│   ├── templates_manager.py    # Message templates (SQLite)
│   ├── workflow_manager.py     # Multi-step workflows (SQLite)
│   ├── db.py                   # SQLiteStore wrapper
│   ├── helpers.py              # Phone normalization, file I/O
│   ├── safety.py               # Campaign safety checks
│   ├── scheduler.py            # Scheduled sending
│   ├── logger.py               # Application logging
│   └── event_log.py            # Diagnostic event formatting
│
├── build/                      # Build tools
│   ├── build.py                # PyInstaller build script
│   └── setup_script.iss        # Inno Setup installer
│
├── data/                       # Static data & browser profiles
│   ├── locales.json            # AR/EN translations
│   ├── metadata.json           # App metadata
│   ├── auto_reply_rules.json   # Chatbot rules
│   └── profiles/               # Chrome user profiles
│
└── tests/                      # Unit tests
    ├── test_config_manager.py
    ├── test_helpers.py
    ├── test_json_managers.py
    ├── test_logger.py
    ├── test_safety.py
    ├── test_db.py
    ├── test_workflow_manager.py
    ├── test_scheduler.py
    ├── test_event_log.py
    └── test_theme.py
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Development

```bash
# Run all tests
python -m unittest discover tests -v

# Compile check (zero errors = OK)
python -m compileall -q main.py gui utils automation tests

# Build executable
python build/build.py
```

## Architecture

The app uses **Python Mixin pattern** to keep large classes organized:

- **`WhatsAppBot`** inherits from 5 mixins (browser, chat, messaging, media, chatbot)
- **`ModernWhatsAppApp`** inherits from 6 mixins (tabs, automation, contacts, reporting, dialogs, progress)

Each mixin shares `self` state via multiple inheritance, keeping files focused and manageable.
