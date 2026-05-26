import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import logger
from gui.modern_ui import ModernWhatsAppApp


def main():
    print(
        "WhatsApp Sender Pro — سجل التشخيص يظهر هنا وفي تبويب «الأحداث» داخل البرنامج.",
        file=sys.stderr,
        flush=True,
    )
    logger.info("WhatsApp Sender Pro starting")
    try:
        app = ModernWhatsAppApp()
        app.mainloop()
    except Exception as exc:
        logger.critical("Application crashed: %s", exc, exc_info=True)
        raise
    finally:
        logger.info("Application shutdown")


if __name__ == "__main__":
    main()
