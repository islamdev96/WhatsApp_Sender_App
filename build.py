"""
Build Script for WhatsApp Sender Pro.
Automates the PyInstaller build process, including adding data files and setting icons.
"""
import PyInstaller.__main__
import os
import shutil
import sys

# Clean previous build
for folder in ("dist", "build"):
    if os.path.exists(folder):
        shutil.rmtree(folder)

for f in [f for f in os.listdir(".") if f.endswith(".spec")]:
    os.remove(f)

# Define build arguments
args = [
    "main.py",  # Entry point
    "--name=WhatsAppSenderPro",
    "--onefile",
    "--windowed",  # Hide console
    "--clean",
    "--noconfirm",
    # Add hidden imports
    "--hidden-import=customtkinter",
    "--hidden-import=PIL",
    "--hidden-import=PIL._tkinter_finder",
    "--hidden-import=openpyxl",
    "--hidden-import=selenium",
    # Add data files (source;dest)
    "--add-data=gui;gui",
    "--add-data=utils;utils",
    "--add-data=automation;automation",
    # Specific files
    "--add-data=requirements.txt;.",
]

# Run PyInstaller
print(f"Building WhatsApp Sender Pro with Python {sys.version}...")
PyInstaller.__main__.run(args)

# Clean up spec file after build
for f in [f for f in os.listdir(".") if f.endswith(".spec")]:
    os.remove(f)

print("\n[SUCCESS] Build complete! Check 'dist/WhatsAppSenderPro.exe'")
