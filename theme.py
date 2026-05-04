"""
theme.py — Color palettes และ Qt Stylesheet สำหรับ Thai Spell Checker
แก้ไขสีหรือ style ที่นี่โดยไม่ต้องแตะ app.py
"""

# ── Color palettes ────────────────────────────────────────────────────────────

DARK = {
    "bg":      "#0F172A",
    "panel":   "#1E293B",
    "border":  "#334155",
    "accent":  "#3B82F6",
    "error":   "#F87171",
    "success": "#34D399",
    "text":    "#F1F5F9",
    "subtext": "#94A3B8",
    "hover":   "#263548",
    "sel":     "#1E3A5F",
    "ctx_bg":  "#0F172A",
    "btn_hover_accent": "#2563EB",
}

LIGHT = {
    "bg":      "#F1F5F9",
    "panel":   "#FFFFFF",
    "border":  "#E2E8F0",
    "accent":  "#2563EB",
    "error":   "#DC2626",
    "success": "#059669",
    "text":    "#1E293B",
    "subtext": "#64748B",
    "hover":   "#F8FAFC",
    "sel":     "#EFF6FF",
    "ctx_bg":  "#F8FAFC",
    "btn_hover_accent": "#1E40AF",
}


def build_qss(c: dict) -> str:
    """สร้าง Qt Stylesheet จาก color palette — เหมือน CSS ของ web"""
    return f"""
    QMainWindow, QWidget#central {{
        background: {c['bg']};
    }}
    QWidget {{
        font-family: 'Segoe UI', 'Tahoma', sans-serif;
        font-size: 14px;
        color: {c['text']};
    }}

    /* ── Top bar ── */
    QLabel#app_title {{
        font-size: 18px;
        font-weight: 700;
    }}
    QLabel#section_label {{
        font-size: 11px;
        font-weight: 600;
        color: {c['subtext']};
        letter-spacing: 1px;
    }}
    QPushButton#browse_btn {{
        background: {c['panel']};
        border: 1.5px solid {c['border']};
        border-radius: 8px;
        padding: 10px 14px;
        color: {c['subtext']};
        text-align: left;
    }}
    QPushButton#browse_btn:hover {{
        border-color: {c['accent']};
        color: {c['text']};
    }}
    QPushButton#check_btn {{
        background: {c['accent']};
        border: none;
        border-radius: 8px;
        padding: 10px 26px;
        color: white;
        font-weight: 700;
    }}
    QPushButton#check_btn:hover {{
        background: {c['btn_hover_accent']};
    }}
    QPushButton#check_btn:disabled {{
        background: {c['border']};
        color: {c['subtext']};
    }}
    QPushButton#theme_btn {{
        background: transparent;
        border: 1.5px solid {c['border']};
        border-radius: 8px;
        padding: 8px 12px;
        color: {c['subtext']};
        font-size: 16px;
    }}
    QPushButton#theme_btn:hover {{
        border-color: {c['accent']};
        color: {c['text']};
    }}

    /* ── Error list (ซ้าย) ── */
    QListWidget {{
        background: {c['panel']};
        border: 1.5px solid {c['border']};
        border-radius: 12px;
        padding: 4px;
        outline: none;
    }}
    QListWidget::item {{
        border-radius: 8px;
        padding: 0;
        margin: 2px 0;
    }}
    QListWidget::item:selected {{
        background: {c['sel']};
    }}
    QListWidget::item:hover:!selected {{
        background: {c['hover']};
    }}

    /* ── Detail panel (ขวา) ── */
    QFrame#detail_panel {{
        background: {c['panel']};
        border: 1.5px solid {c['border']};
        border-radius: 12px;
    }}
    QFrame#divider {{
        background: {c['border']};
        max-height: 1px;
    }}
    QLabel#wrong_word {{
        font-size: 26px;
        font-weight: 700;
        color: {c['error']};
    }}
    QLabel#best_word {{
        font-size: 26px;
        font-weight: 700;
        color: {c['success']};
    }}
    QLabel#arrow_label {{
        font-size: 20px;
        color: {c['subtext']};
        padding: 0 8px;
    }}
    QTextBrowser#ctx_box {{
        background: {c['ctx_bg']};
        border: 1.5px solid {c['border']};
        border-radius: 8px;
        color: {c['text']};
        padding: 10px;
        font-size: 14px;
    }}
    QPushButton#sug_btn {{
        background: transparent;
        border: 1.5px solid {c['accent']};
        border-radius: 14px;
        padding: 4px 14px;
        color: {c['accent']};
        font-size: 13px;
    }}
    QPushButton#sug_btn:hover {{
        background: {c['accent']};
        color: white;
    }}

    /* ── Empty panel ── */
    QFrame#empty_panel {{
        background: {c['panel']};
        border: 1.5px solid {c['border']};
        border-radius: 12px;
    }}
    QLabel#empty_hint {{
        color: {c['subtext']};
        font-size: 15px;
    }}

    /* ── Status bar ── */
    QStatusBar {{
        background: {c['bg']};
        color: {c['subtext']};
        border-top: 1px solid {c['border']};
        font-size: 13px;
        padding: 4px 8px;
    }}

    /* ── Scrollbar ── */
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {c['border']};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    /* ── Splitter ── */
    QSplitter::handle {{
        background: {c['border']};
        width: 1px;
        margin: 8px 0;
    }}
    """
