# WhatsApp Sender Pro - Installation Guide

## 1. Standalone Executable
You can find the standalone application in the `dist` folder:
- `dist\WhatsAppSenderPro.exe`

You can move this file anywhere and run it. It contains all necessary dependencies.

## 2. Creating the Installer (Optional)
To create a professional installer like other Windows apps:

1. Download and install **Inno Setup** from: https://jrsoftware.org/isdl.php
2. Open the file `setup_script.iss` in this folder.
3. Click the **Compile** button (or Run).
4. The installer `WhatsAppSenderPro_Setup_v2.5.exe` will be generated in this folder.

## Notes
- The first launch might be slightly slower as it extracts internal files.
- Ensure you have Chrome installed for the WhatsApp automation to work.
- The app data (settings, templates, campaigns) will be saved in your local user folder.
