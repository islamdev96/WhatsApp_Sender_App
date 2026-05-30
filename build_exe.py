"""WhatsApp Sender Pro — Automated PyInstaller Standalone EXE Build Script.

Handles all CustomTkinter assets, data locales, and automated packaging requirements.
"""
import os
import sys
import subprocess
import shutil


def main():
    print("Starting WhatsApp Sender Pro packaging script...")
    
    # 1. Ensure pyinstaller is installed
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
    # 2. Get CustomTkinter directory path
    try:
        import customtkinter
        ctk_path = os.path.dirname(customtkinter.__file__)
        print(f"Found CustomTkinter at: {ctk_path}")
    except ImportError:
        print("Installing CustomTkinter...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
        import customtkinter
        ctk_path = os.path.dirname(customtkinter.__file__)

    # 3. Clean up previous build directories
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            print(f"Cleaning up existing '{folder}' directory...")
            try:
                shutil.rmtree(folder)
            except Exception as e:
                print(f"Warning: Could not fully delete '{folder}': {e}")

    # 4. Formulate PyInstaller command
    # CustomTkinter needs its asset files copied (themes, fonts, etc.)
    # Format for PyInstaller add-data is: "source_path;destination_path" on Windows
    ctk_data = f"{ctk_path};customtkinter"
    
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--noconfirm",
        "--name=WhatsAppSenderPro",
        f"--add-data={ctk_data}",
        f"--add-data=data/locales.json;data",
        f"--add-data=automation/selectors.json;automation",
        "--add-data=data/auto_reply_rules.json;data",
        "--add-data=data/app_logo.png;data",
        "--icon=data/app_icon.ico",
        "main.py"
    ]
    
    print(f"Running PyInstaller command:\n{' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        print("\nSUCCESS! Application packaged successfully inside 'dist/WhatsAppSenderPro/'!")
        print("You can run 'dist/WhatsAppSenderPro/WhatsAppSenderPro.exe' directly on any Windows PC.")
    except subprocess.CalledProcessError as e:
        print(f"\nError: PyInstaller packaging failed with code: {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
