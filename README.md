# 🟢 Auto WhatsApp Business Sender Turbo Pro v17.0 Full

> Professional, premium, and fully-featured WhatsApp marketing automation software built with a modern **CustomTkinter** UI and robust **Selenium** automation. Works natively on Windows as a standalone `.exe` without license prompts or external Python setups.

---

## 📖 جدول المحتويات | Table of Contents
* [الميزات الرئيسية | Key Features](#-الميزات-الرئيسية--key-features)
* [البنية الهيكلية للمشروع | Project Architecture](#-البنية-الهيكلية-للمشروع--project-architecture)
* [دليل البدء السريع | Quick Start](#-دليل-البدء-السريع--quick-start)
* [التجميع والإنتاج | Standalone Bundling](#-التجميع-والإنتاج--standalone-bundling)
* [الاختبارات والتحقق | Verification & Tests](#-الاختبارات-والتحقق--verification--tests)

---

## 🌟 الميزات الرئيسية | Key Features

### 🇸🇦 دعم كامل للثنائية اللغوية والسمات | Bilingual & Theme Engine
* **Multilingual UI (AR/EN):** Real-time interface translation toggle preserving layout constraints.
* **Premium Theme Mode:** Sleepy dark slate (`#0F172A`) and emerald green (`#00E676`) aesthetic matching professional modern software trends. Supports instant dark/light toggles.

### 🛡️ أمان فائق وضد الحظر | Advanced Anti-Ban Protections
* **Intelligent Spintax Engine:** Resolves message templates rotation like `{Hi|Hello|Welcome} client, your code is {A|B}.` dynamically per recipient.
* **Assessors & Batch Pauses:** Preflight safety algorithms checking batch delay safety limits dynamically.
* **Rotational Profiles:** Integrates proxy extension generators and browser fingerprint alterations (User-Agent viewport changes) for complete stealth.

### 🗺️ أدوات تسويقية متكاملة | Integrated Marketing Utilities
* **Google Maps Scraper:** Direct live business lead extraction with instant phone number harvesting and single-click campaign importing.
* **Campaign Date-Time Scheduler:** Full polling future scheduler persistence in SQLite database.
* **Contacts Management:** Interactive SQLite list manager with file preview sniffer.

---

## 🏗️ البنية الهيكلية للمشروع | Project Architecture

The codebase uses a highly modular, decoupled **Python Mixin Pattern** and standalone `CTkToplevel` dialogue classes to minimize monolith file sizes:

```
WhatsApp_Sender_App/
├── main.py                     # App bootstrap entry point
├── build_exe.py                # Automated PyInstaller packaging compiler
├── WhatsAppSenderPro.zip       # Final zipped executable distribution release
│
├── automation/                 # Selenium WhatsApp Automation Engine
│   ├── bot.py                  # Core WhatsAppBot lifecycle and thread runner
│   ├── browser_setup.py        # Chrome WebDriver profile and browser launching
│   ├── chat_navigation.py      # Navigation selectors and number checks
│   ├── messaging.py            # Message dispatching, spintax, and caption hooks
│   ├── media_handler.py        # Files, videos, and photos thumbnail attachment handler
│   ├── chatbot.py              # Keyword pattern rules unread reply bot
│   └── selectors.json          # Live CSS/XPath selectors database
│
├── gui/                        # Premium CustomTkinter UI Package
│   ├── app.py                  # Main Window controller, thread safe UI queue and Splash Screen
│   ├── theme.py                # HSL harmonized theme tokens & error catalog
│   ├── components.py           # Custom interactive treeviews and attachments manager
│   │
│   ├── dialogs/                # Standalone popup widget windows [MODULAR]
│   │   ├── import_dialog.py    # CSV/Excel preview sniffer & column-mapper
│   │   ├── num_gen_dialog.py   # Phone list sequential generator popup
│   │   ├── schedule_dialog.py  # Future campaigns Date-Time scheduler picker
│   │   └── activation_dialog.py# Pre-activated license key dialog
│   │
│   └── mixins/                 # Logic handlers split by concern
│       ├── tab_builders.py     # Tab builders & layout grid constructor
│       ├── automation_mixin.py # Campaigns send/pause/stop runner logic
│       ├── contacts_mixin.py   # Clean contact lists and template spin logic
│       ├── progress_mixin.py   # Large active campaign monitor mixin
│       └── reporting_mixin.py  # Campaign logs exporter & CSV reports
│
├── utils/                      # Database and Core Helpers Package
│   ├── db.py                   # SQLite Store CRUD controller
│   ├── campaign_manager.py     # Campaign persistence manager
│   ├── contacts_manager.py     # Saved contact groups and lists
│   ├── templates_manager.py    # Saved message template text rules
│   ├── safety.py               # Preflight safety limits assessor
│   ├── scheduler.py            # Time polling future cron/daemon engine
│   └── helpers/                # Sub-package for normalization & cleanups
│
└── tests/                      # 63 Core Pytest/Unittest validation suites
```

---

## 🚀 دليل البدء السريع | Quick Start

### 1. النسخة المستقلة الجاهزة (Direct Standalone Run)
لا تحتاج لتثبيت أي برامج أو بيئة بايثون!
* قم بفك ضغط ملف **[WhatsAppSenderPro.zip](file:///c:/Users/Islam%20Glab/Desktop/WhatsApp_Sender_App/WhatsAppSenderPro.zip)**.
* افتح المجلد الناتج واضغط نقرتين على `WhatsAppSenderPro.exe` للتشغيل الفوري مع شاشة ترحيبية فاخرة.

### 2. وضع التطوير والبرمجة (Development Mode)
إذا أردت تشغيل وتعديل الكود المصدري:

```bash
# تثبيت المكتبات والمتطلبات البرمجية
pip install -r requirements.txt

# تشغيل التطبيق الرئيسي
python main.py
```

---

## 📦 التجميع والإنتاج | Standalone Bundling

تم إعداد ملف بناء تلقائي شامل يقوم بتجميع كافة الخطوط، اللغات، ترجمات الترشيح والأكواد التابعة لـ CustomTkinter في ملف تشغيل مستقل:

```powershell
python build_exe.py
```

ينتج عن هذا الملف مجلد تشغيل متكامل داخل `dist/WhatsAppSenderPro/` والذي تم ضغطه بالكامل في ملف **[WhatsAppSenderPro.zip](file:///c:/Users/Islam%20Glab/Desktop/WhatsApp_Sender_App/WhatsAppSenderPro.zip)** لتسهيل نقله وتوزيعه.

---

## 🧪 الاختبارات والتحقق | Verification & Tests

لضمان سلامة جميع فلاتر الحظر، إدارة قواعد البيانات، ومحرك الجدولة، يمكنك تشغيل الاختبارات البرمجية الشاملة المدمجة:

```powershell
python -m unittest discover -s tests
```
> [!NOTE]
> **63 اختبارًا تلقائيًا** تعمل وتجتاز بالكامل بنسبة نجاح **100%** في أقل من 1.4 ثانية!
