TIER_LIST = [
    "언랭크",
    "아이언",
    "브론즈",
    "실버",
    "골드",
    "플래티넘",
    "에메랄드",
    "다이아",
    "마스터",
]

POSITIONS = [
    "탑",
    "정글",
    "미드",
    "원딜",
    "서포터",
]

ANY_POSITION = "상관없음"

POSITION_OPTIONS = [
    ANY_POSITION,
    *POSITIONS,
]

DEFAULT_TIER_SCORE = {
    "아이언": 1,
    "브론즈": 2,
    "실버": 3,
    "골드": 4,
    "플래티넘": 5,
    "에메랄드": 6,
    "다이아": 7,
    "마스터": 8,
}

DEFAULT_BUILD_WEIGHTS = {
    "team_diff": 10,
    "line_diff_total": 6,
    "position_penalty": 3,
    "bottom_penalty": 2,
    "team_form_diff": 8,
    "couple_group_penalty": 12,
}

DEFAULT_SERVER_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_THEME_MODE = "dark"
ACCOUNT_SEARCH_LIMIT = 1000

THEME_LABELS = {
    "dark": "다크 모드",
    "light": "화이트 모드",
}

TIER_ALIASES = {
    "unranked": "언랭크",
    "iron": "아이언",
    "bronze": "브론즈",
    "silver": "실버",
    "gold": "골드",
    "platinum": "플래티넘",
    "emerald": "에메랄드",
    "diamond": "다이아",
    "master": "마스터",
    "?꾩씠??": "아이언",
    "釉뚮줎利?": "브론즈",
    "?ㅻ쾭": "실버",
    "怨⑤뱶": "골드",
    "?뚮옒?곕꽆": "플래티넘",
    "?먮찓?꾨뱶": "에메랄드",
    "?ㅼ씠??": "다이아",
    "留덉뒪??": "마스터",
}

POSITION_ALIASES = {
    "top": "탑",
    "jungle": "정글",
    "mid": "미드",
    "middle": "미드",
    "adc": "원딜",
    "bottom": "원딜",
    "bot": "원딜",
    "support": "서포터",
    "utility": "서포터",
    "fill": ANY_POSITION,
    "any": ANY_POSITION,
    "??": "탑",
    "?뺢?": "정글",
    "誘몃뱶": "미드",
    "?먮뵜": "원딜",
    "?쒗룷??": "서포터",
    "?곴??놁쓬": ANY_POSITION,
}


def normalize_tier_name(value):
    text = (value or "").strip()
    if text == "언랭크":
        return text

    if text in DEFAULT_TIER_SCORE:
        return text

    normalized = TIER_ALIASES.get(text.lower())
    if normalized:
        return normalized

    normalized = TIER_ALIASES.get(text)
    if normalized:
        return normalized

    return text or "언랭크"


def normalize_position_name(value):
    text = (value or "").strip()
    if text in POSITION_OPTIONS:
        return text

    lowered = text.lower()
    if lowered in POSITION_ALIASES:
        return POSITION_ALIASES[lowered]

    if text in POSITION_ALIASES:
        return POSITION_ALIASES[text]

    return text or ANY_POSITION


def normalize_theme_mode(value):
    return "light" if str(value).strip().lower() == "light" else DEFAULT_THEME_MODE
