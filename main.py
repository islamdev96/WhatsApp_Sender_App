import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.modern_ui import ModernWhatsAppApp


def main():
    app = ModernWhatsAppApp()
    app.mainloop()


if __name__ == "__main__":
    main()
