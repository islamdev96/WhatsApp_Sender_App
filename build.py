"""
Build Script for WhatsApp Sender Pro.
Automates the PyInstaller build process, including adding data files and setting icons.
"""
import PyInstaller.__main__
import os
import shutil

# Clean previous build
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")

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
print("Building WhatsApp Sender Pro...")
PyInstaller.__main__.run(args)

print("\nBuild complete! Check 'dist/WhatsAppSenderPro.exe'")
