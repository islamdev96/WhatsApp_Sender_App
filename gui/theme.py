"""
WhatsApp Sender Pro — Theme constants.
Color palettes, typography, and error catalog.
"""
# ─── Color Palette (Premium) ────────────────────────────────────────────────
PALETTE_DARK = {
    # Main branding
    "primary":       "#00FF9D",  # Ultra-Premium Glowing Neon Emerald Green
    "primary_hover": "#00E676",  # Soft green hover transition
    "primary_dark":  "#070B14",  # Rich deep midnight base background

    # Status colors
    "danger":        "#F43F5E",
    "danger_hover":  "#E11D48",
    "warning":       "#F59E0B",
    "success":       "#00FF9D",  # Neon green success indicator
    "success_hover": "#00E676",
    "info":          "#00E5FF",  # Cyber cyan info indicator

    # UI Elements (Premium Midnight depth layering)
    "card_bg":       "#121B2E",  # Floating Indigo-Slate card background
    "bg_dark":       "#080C14",  # Deep space dark base background
    "text_main":     "#F9FAFB",  # Crisp high-contrast frost white text
    "text_muted":    "#94A3B8",  # Soft slate-grey text
    "accent":        "#00FF9D",  # Glowing Neon green accent
    "accent_hover":  "#00E676",
    "border":        "#1E2B45",  # Subtle outline indigo border
    "secondary":     "#17233C",  # Stylish secondary button slate-blue
    "secondary_hover":"#203154",
    "secondary_text":"#F9FAFB",

    # Sidebar navigation (SaaS design, fully unified with deep base)
    "sidebar_bg":     "#070B14",  # Match deep midnight base
    "sidebar_hover":  "#121B2E",  # Hover matches card background
    "sidebar_active": "#1C2A4A",  # Active item slate-indigo
    "sidebar_text":   "#F9FAFB",
    "sidebar_icon":   "#00FF9D",  # Glowing green icons
    "sidebar_separator": "#121B2E",
    "topbar_bg":      "#070B14",  # Match deep space header background
}

PALETTE_LIGHT = {
    # Main branding
    "primary":       "#008069",  # WhatsApp Premium Light Teal Green
    "primary_hover": "#006653",
    "primary_dark":  "#F8FAFC",  # Slate light base

    # Status colors
    "danger":        "#E11D48",
    "danger_hover":  "#BE123C",
    "warning":       "#D97706",
    "success":       "#008069",
    "success_hover": "#006653",
    "info":          "#0284C7",

    # UI Elements (Gorgeous Slate light contrast)
    "card_bg":       "#FFFFFF",  # Layered white card background
    "bg_dark":       "#F1F5F9",  # High-quality light slate background
    "text_main":     "#0F172A",  # Rich deep slate text
    "text_muted":    "#64748B",  # Slate muted text
    "accent":        "#027EB5",
    "accent_hover":  "#015F8A",
    "border":        "#E2E8F0",  # High-quality light borders
    "secondary":     "#F8FAFC",  # Elegant light buttons
    "secondary_hover":"#E2E8F0",
    "secondary_text":"#0F172A",

    # Sidebar navigation (Premium high-contrast green theme)
    "sidebar_bg":     "#128C7E",  # WhatsApp medium green
    "sidebar_hover":  "#0F7A6E",  # Darker green on hover
    "sidebar_active": "#006653",  # Deep green for supreme active tab contrast
    "sidebar_text":   "#E9EDEF",  # Clean silver-white text
    "sidebar_icon":   "#E8F5E9",
    "sidebar_separator": "#1A9E8F",
    "topbar_bg":      "#FFFFFF",  # White topbar background
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


