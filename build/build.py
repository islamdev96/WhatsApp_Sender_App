"""
Build Script for WhatsApp Sender Pro.
Automates the PyInstaller build process, including adding data files and setting icons.
Run from the project ROOT directory: python build/build.py
"""
import PyInstaller.__main__
import os
import shutil
import sys

# Ensure we're running from project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)

# Clean previous build
for folder in ("dist", "build_tmp"):
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
    "--add-data=data;data",
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
