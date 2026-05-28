"""Report and temporary file cleanup utilities."""
import os
from utils.logger import logger


def cleanup_old_reports(reports_base_dir=None, max_age_days=30):
    """Delete report files (CSV/TXT) older than *max_age_days*.

    Scans `reports/` and `reports/number_checks/` for stale files
    and removes them to prevent unbounded disk usage.

    Returns the number of files removed.
    """
    import time

    if reports_base_dir is None:
        reports_base_dir = os.path.join(os.getcwd(), "reports")
    if not os.path.isdir(reports_base_dir):
        return 0

    cutoff = time.time() - (max_age_days * 86400)
    removed = 0
    scan_dirs = [reports_base_dir]

    # Also scan known subdirectories
    for sub in ("number_checks", "logs"):
        sub_path = os.path.join(reports_base_dir, sub)
        if os.path.isdir(sub_path):
            scan_dirs.append(sub_path)

    for dir_path in scan_dirs:
        try:
            for entry in os.scandir(dir_path):
                if not entry.is_file():
                    continue
                ext = os.path.splitext(entry.name)[1].lower()
                if ext not in (".csv", ".txt", ".log"):
                    continue
                try:
                    if entry.stat().st_mtime < cutoff:
                        os.unlink(entry.path)
                        removed += 1
                except OSError as exc:
                    logger.debug("Could not remove old report %s: %s", entry.path, exc)
        except OSError as exc:
            logger.debug("Could not scan reports directory %s: %s", dir_path, exc)

    if removed:
        logger.info("Cleaned up %d old report file(s) from %s", removed, reports_base_dir)
    return removed

