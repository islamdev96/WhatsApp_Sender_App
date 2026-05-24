import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.modern_ui import ModernWhatsAppApp


def main():
    import sys

    print(
        "WhatsApp Sender Pro — سجل التشخيص يظهر هنا وفي تبويب «الأحداث» داخل البرنامج.",
        file=sys.stderr,
        flush=True,
    )
    app = ModernWhatsAppApp()
    app.mainloop()


if __name__ == "__main__":
    main()
