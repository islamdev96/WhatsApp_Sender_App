import logging
import logging.handlers
import os
from datetime import datetime

LOG_DIR = os.path.join(os.getcwd(), "logs")
LOG_FILE_MAX_BYTES = 5 * 1024 * 1024
LOG_FILE_BACKUP_COUNT = 3


def setup_logger(name="whatsapp_sender", level=logging.INFO):
    """Create the application logger once and reuse it everywhere."""
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))

    log_file = os.path.join(LOG_DIR, f"whatsapp_sender_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=LOG_FILE_MAX_BYTES,
        backupCount=LOG_FILE_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    )

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


logger = setup_logger()


def log_error(message, exc=None, level=logging.ERROR):
    if exc is not None:
        logger.log(level, "%s: %s", message, exc, exc_info=True)
    else:
        logger.log(level, message)


def log_exception(message, exc):
    logger.exception("%s: %s", message, exc)
