from domain.constants import DEFAULT_THEME_MODE, normalize_theme_mode


TIER_COLOR = {
    "아이언": "#7f8c8d",
    "브론즈": "#c17f59",
    "실버": "#bdc3c7",
    "골드": "#f1c40f",
    "플래티넘": "#48c9b0",
    "에메랄드": "#2ecc71",
    "다이아": "#5dade2",
    "마스터": "#c56cf0",
}


THEME_TOKENS = {
    "dark": {
        "recent_summary_text": "#d9e6ff",
        "recent_summary_bg": "#1f2c3a",
        "recent_summary_border": "#35516b",
        "muted_text": "#d8dee9",
        "team1_score": "#e74c3c",
        "team2_score": "#3498db",
        "diff_text": "#5dade2",
        "result_name_bg": "#ffffff",
        "result_name_fg": "#000000",
        "table_gridline": "#404040",
        "table_alt_bg": "#20242b",
        "table_bg": "#171a20",
        "table_selected_bg": "#35516b",
        "row_selected_border": "#ffd966",
        "row_default_border": "#4a4a4a",
        "row_selected_bg": "#253546",
        "row_default_bg": "#1f1f1f",
        "input_text": "#ffffff",
        "tier_text": "#000000",
    },
    "light": {
        "recent_summary_text": "#27415d",
        "recent_summary_bg": "#eef6ff",
        "recent_summary_border": "#b7d1ec",
        "muted_text": "#31475e",
        "team1_score": "#c0392b",
        "team2_score": "#2471a3",
        "diff_text": "#2874a6",
        "result_name_bg": "#ffffff",
        "result_name_fg": "#1f2933",
        "table_gridline": "#c8d3df",
        "table_alt_bg": "#f7f9fc",
        "table_bg": "#ffffff",
        "table_selected_bg": "#dcecff",
        "row_selected_border": "#f0b429",
        "row_default_border": "#cbd5e1",
        "row_selected_bg": "#eaf3ff",
        "row_default_bg": "#ffffff",
        "input_text": "#1f2933",
        "tier_text": "#111111",
    },
}


def get_theme_tokens(theme_mode):
    normalized = normalize_theme_mode(theme_mode)
    return THEME_TOKENS.get(normalized, THEME_TOKENS[DEFAULT_THEME_MODE])


def get_recent_summary_style(theme_mode):
    tokens = get_theme_tokens(theme_mode)
    return (
        "font-size: 14px; font-weight: bold; "
        f"color: {tokens['recent_summary_text']}; "
        f"background-color: {tokens['recent_summary_bg']}; "
        f"border: 1px solid {tokens['recent_summary_border']}; "
        "border-radius: 6px; padding: 8px;"
    )
