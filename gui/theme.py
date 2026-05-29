"""
WhatsApp Sender Pro — Theme constants.
Color palettes, typography, and error catalog.
"""
# ─── Color Palette (Premium) ────────────────────────────────────────────────
PALETTE_DARK = {
    # Main branding
    "primary":       "#00A884",  # WhatsApp Premium Teal Green
    "primary_hover": "#008F6F",
    "primary_dark":  "#000000",  # Pitch-black base

    # Status colors
    "danger":        "#F43F5E",
    "danger_hover":  "#E11D48",
    "warning":       "#F59E0B",
    "success":       "#00A884",
    "success_hover": "#008F6F",
    "info":          "#38BDF8",

    # UI Elements (High contrast, flat)
    "card_bg":       "#000000",  # Pitch black for cards
    "bg_dark":       "#000000",  # Pitch black for frames
    "text_main":     "#FFFFFF",  # High-contrast white text
    "text_muted":    "#A0A0A0",  # Muted grey text
    "accent":        "#00E676",
    "accent_hover":  "#00C853",
    "border":        "#333333",  # Dark grey borders
    "secondary":     "#121212",  # Dark buttons
    "secondary_hover":"#1A1A1A",
    "secondary_text":"#FFFFFF",
}

PALETTE_LIGHT = {
    # Main branding
    "primary":       "#008069",  # WhatsApp Premium Light Teal Green
    "primary_hover": "#006653",
    "primary_dark":  "#F0F2F5",  # Light grey-blue

    # Status colors
    "danger":        "#E11D48",
    "danger_hover":  "#BE123C",
    "warning":       "#D97706",
    "success":       "#008069",
    "success_hover": "#006653",
    "info":          "#0284C7",

    # UI Elements
    "card_bg":       "#F0F2F5",
    "bg_dark":       "#FFFFFF",
    "text_main":     "#111B21",  # Deep charcoal text
    "text_muted":    "#667781",  # Sleek muted grey
    "accent":        "#027EB5",
    "accent_hover":  "#015F8A",
    "border":        "#E9EDF0",
    "secondary":     "#E9EDF0",
    "secondary_hover":"#D1D7DB",
    "secondary_text":"#111B21",
}

# Active palette (filled at runtime based on appearance mode)
COLORS = {}

# ─── Typography & Styling ─────────────────────────────────────────────────────
FONTS = {
    "header": ("Segoe UI", 24, "bold"),
    "sub_header": ("Segoe UI", 16, "bold"),
    "body": ("Segoe UI", 13),
    "body_bold": ("Segoe UI", 13, "bold"),
    "small": ("Segoe UI", 11),
    "mono": ("Consolas", 12),
}

ERROR_CATALOG = {
    "ERR-01": "تعذر تشغيل المتصفح. اغلق كل نوافذ Chrome ثم أعد المحاولة.",
    "ERR-02": "المتصفح لا يستجيب للأتمتة أو انتهت مهلة تسجيل الدخول.",
    "ERR-03": "مشكلة في ملف الأرقام (غير موجود/مفتوح/أعمدة غير صحيحة).",
    "ERR-04": "نص الرسالة فارغ.",
    "ERR-05": "يرجى اختيار ملف أرقام صحيح أو مجموعة.",
    "ERR-09": "ملف الصورة غير موجود أو غير صالح.",
    "ERR-06": "زر الإرفاق غير موجود.",
    "ERR-07": "زر الإرسال لم يظهر في الوقت المحدد.",
    "ERR-08": "فشل رفع الصورة أو كتابة الكابشن.",
    "ERR-10": "انتهت مهلة تحميل المحادثة.",
    "ERR-20": "الرقم غير صحيح أو ليس لديه واتساب.",
    "ERR-21": "لم يتم تسجيل الدخول بعد.",
    "ERR-11": "ملف المتصفح الشخصي قيد الاستخدام حالياً. يرجى إغلاق أي متصفح كروم آخر مفتوح بواسطة هذا الحساب وإعادة المحاولة.",
    "ERR-99": "خطأ غير متوقع.",
}


