"""
Campaign safety helpers — reduce automation risk and align with conservative sending.
Not a guarantee against WhatsApp restrictions; users must follow WhatsApp Terms of Service.
"""
from __future__ import annotations

import os
from utils.logger import logger

# Conservative defaults (seconds)
MIN_DELAY_SECONDS = 15
RECOMMENDED_DELAY_MIN = 30
RECOMMENDED_DELAY_MAX = 120
MIN_BATCH_PAUSE_SECONDS = 60
MAX_MESSAGES_PER_HOUR_SOFT = 45
MAX_MESSAGES_PER_SESSION_SOFT = 200


def normalize_media_type(att_type: str, path: str = "") -> str:
    """Map attachment type to bot categories: image | video | document."""
    t = (att_type or "document").lower().strip()
    ext = os.path.splitext(path or "")[1].lower()
    if t in ("image", "video", "document"):
        if t != "document":
            return t
    if ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"):
        return "image"
    if ext in (".mp4", ".avi", ".mov", ".mkv", ".3gp", ".webm"):
        return "video"
    return "document"


def extra_delay_after_attachment(att_type: str, path: str = "") -> float:
    """Additional pause after media upload/send (heavier for video/large files)."""
    t = normalize_media_type(att_type, path)
    if t == "document":
        return 4.0
    if t == "video":
        base = 8.0
        try:
            size_mb = os.path.getsize(path) / (1024 * 1024)
            base += min(20.0, size_mb * 2.0)
        except OSError as exc:
            logger.debug("Could not inspect attachment size for %s: %s", path, exc)
        return base
    if t == "image":
        return 5.0
    return 3.0


def assess_campaign_settings(
    contact_count: int,
    delay_min: float,
    delay_max: float,
    batch_size: int,
    batch_pause_min: float,
    has_media: bool = False,
) -> dict:
    """
    Returns {ok, warnings, suggested_delay_min, suggested_delay_max}.
    """
    warnings = []
    ok = True

    if delay_min < MIN_DELAY_SECONDS:
        warnings.append(
            f"التأخير الأدنى ({delay_min}s) منخفض جداً — يُنصح بـ {MIN_DELAY_SECONDS}s على الأقل لتقليل مخاطر الحظر."
        )
        ok = False

    if delay_max < delay_min:
        warnings.append("التأخير الأقصى أصغر من الأدنى — سيتم تبديلهما.")
        ok = False

    if batch_size > 0 and batch_pause_min < MIN_BATCH_PAUSE_SECONDS:
        warnings.append(
            f"استراحة الدفعة ({batch_pause_min}s) قصيرة — يُنصح بـ {MIN_BATCH_PAUSE_SECONDS}s أو أكثر."
        )

    if contact_count > MAX_MESSAGES_PER_SESSION_SOFT:
        warnings.append(
            f"عدد جهات الاتصال ({contact_count}) كبير — قسّم الحملة إلى دفعات أصغر (≤{MAX_MESSAGES_PER_SESSION_SOFT})."
        )

    if has_media and delay_min < RECOMMENDED_DELAY_MIN:
        warnings.append(
            f"إرسال وسائط يتطلب تأخيراً أطول — يُنصح بـ {RECOMMENDED_DELAY_MIN}-{RECOMMENDED_DELAY_MAX} ثانية."
        )

    est_per_hour = 3600.0 / max(delay_min, 1) if delay_min else 999
    if est_per_hour > MAX_MESSAGES_PER_HOUR_SOFT:
        warnings.append(
            f"المعدل التقريبي (~{int(est_per_hour)} رسالة/ساعة) مرتفع — الهدف الآمن: ≤{MAX_MESSAGES_PER_HOUR_SOFT}/ساعة."
        )

    suggested_min = max(float(delay_min), MIN_DELAY_SECONDS)
    if has_media:
        suggested_min = max(suggested_min, RECOMMENDED_DELAY_MIN)
    suggested_max = max(float(delay_max), suggested_min + 10, RECOMMENDED_DELAY_MAX if has_media else suggested_min + 30)

    return {
        "ok": ok,
        "warnings": warnings,
        "suggested_delay_min": suggested_min,
        "suggested_delay_max": suggested_max,
    }
