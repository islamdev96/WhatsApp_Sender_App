# 🟢 WhatsApp Sender Pro

> Professional, premium, and fully-featured WhatsApp marketing automation software built with a native **C# / WPF** UI and robust **Microsoft Edge WebView2** automation. Works natively on Windows with database storage in **SQLite** and modular dialog workflow options.

---

## 📖 جدول المحتويات | Table of Contents
* [الميزات الرئيسية | Key Features](#-الميزات-الرئيسية--key-features)
* [البنية الهيكلية للمشروع | Project Architecture](#-البنية-الهيكلية-للمشروع--project-architecture)
* [دليل البدء السريع | Quick Start](#-دليل-البدء-السريع--quick-start)
* [الاختبارات والتحقق | Verification & Tests](#-الاختبارات-والتحقق--verification--tests)

---

## 🌟 الميزات الرئيسية | Key Features

### 🇸🇦 دعم كامل للثنائية اللغوية والسمات | Bilingual & Theme Engine
* **Multilingual UI (AR/EN):** Real-time interface translation toggle preserving layout constraints and RTL/LTR formatting.
* **Premium Theme Mode:** Sleepy dark slate and emerald green aesthetic matching professional modern software trends. Supports instant dark/light toggles.

### 🛡️ أمان فائق وضد الحظر | Advanced Anti-Ban Protections
* **Intelligent Spintax Engine:** Resolves message templates rotation like `{Hi|Hello|Welcome} client` dynamically per recipient.
* **Random Delays:** Customizable safe delay margins (e.g. 15-30 seconds) between messages.
* **Multi-Message Campaigning:** Rotate between multiple different message drafts to avoid WhatsApp detection algorithms.
* **Account Warmer:** Automatic message exchange system between friendly accounts to warm up new profiles.

### 🗺️ أدوات تسويقية متكاملة | Integrated Marketing Utilities
* **Google Maps Scraper:** Direct live business lead extraction using WebView2 with single-click campaign importing.
* **Campaign Date-Time Scheduler:** Full polling future scheduler persistence in SQLite database.
* **Contacts Management:** Interactive SQLite list manager with file import.
* **Drip Workflows Builder:** Design sequential messaging pipelines (e.g. Day 1: Welcome, Day 3: Promo, Day 5: Follow-up).
* **WhatsApp Numbers Filter:** Instantly check WhatsApp presence for lists of numbers.

---

## 🏗️ البنية الهيكلية للمشروع | Project Architecture

The codebase consists of three sub-projects:

```
WhatsApp_Sender_App/
├── WhatsAppSenderPro.sln         # Main C# Solution file
│
├── WhatsAppSender.Core/          # Services & Data Library
│   ├── Automation/
│   │   ├── IWhatsAppService.cs   # Automation service interface
│   │   ├── WhatsAppAutomationService.cs # WebView2 automation engine
│   │   └── selectors.json        # CSS/XPath selectors database for WhatsApp Web
│   ├── Data/
│   │   ├── Database.cs           # SQLite database connection setup
│   │   ├── ContactsRepository.cs # Saved groups & contacts CRUD repo
│   │   ├── CampaignsRepository.cs# Campaign history logging repo
│   │   ├── TemplatesRepository.cs# Message templates repo
│   │   └── ScheduledCampaignsRepository.cs # Scheduler queue repo
│   ├── Services/
│   │   ├── CampaignRunner.cs     # Background campaign sender loop
│   │   ├── SpintaxEngine.cs      # Spintax spinning template parser
│   │   ├── SchedulerService.cs   # Cron-like campaign schedule daemon
│   │   ├── SafetyService.cs      # Speed limit safety check service
│   │   └── LicensingService.cs   # HWID-based activation license check
│   └── Models/                   # Plain C# Entities (Campaign, Contact, etc.)
│
├── WhatsAppSender.App/           # WPF GUI Project
│   ├── ViewModels/
│   │   ├── MainWindowViewModel.cs# Coordinator & connection monitor
│   │   ├── MainTabViewModel.cs   # Main campaign sending VM
│   │   └── TabViewModels.cs      # ViewModel for sub-dialog windows
│   ├── Resources/
│   │   ├── Ar.xaml               # Arabic localization strings
│   │   ├── En.xaml               # English localization strings
│   │   └── DarkTheme.xaml        # Slate Dark global colors resource
│   ├── Themes/
│   │   └── Styles.xaml           # Reusable controls styling definitions
│   └── Windows/                  # Modular view dialogs
│       ├── MainWindow.xaml       # Single-window 3-column dense dashboard
│       ├── CampaignsHistoryWindow.xaml
│       ├── ContactsManagerWindow.xaml
│       ├── TemplatesManagerWindow.xaml
│       ├── SchedulerWindow.xaml
│       ├── GMapsScraperWindow.xaml
│       ├── WarmerWindow.xaml
│       ├── WorkflowsWindow.xaml
│       └── NumbersFilterWindow.xaml
│
└── WhatsAppSender.Tests/         # Unit Tests Project
    └── CoreServicesTests.cs      # xUnit validation suite
```

---

## 🚀 دليل البدء السريع | Quick Start

### 1. تشغيل التطبيق (Run Application)
افتح **PowerShell** في مجلد المشروع وشغل الأمر التالي:

```powershell
.\dotnet-sdk\dotnet.exe run --project WhatsAppSender.App
```

### 2. البناء وإعادة الإنتاج (Build & Compile)
لبناء ملفات المشروع بأكملها والتحقق من سلامتها:

```powershell
.\dotnet-sdk\dotnet.exe build WhatsAppSenderPro.sln
```

---

## 🧪 الاختبارات والتحقق | Verification & Tests

لتشغيل اختبارات الوحدة المتكاملة للتأكد من سلامة منطق العمليات:

```powershell
.\dotnet-sdk\dotnet.exe test WhatsAppSender.Tests
```
