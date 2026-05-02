TIER_LIST = [
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

DEFAULT_SERVER_BASE_URL = "http://127.0.0.1:8000"

TIER_COLOR = {
    "아이언": "#6e6e6e",
    "브론즈": "#b87333",
    "실버": "#c0c0c0",
    "골드": "#ffd700",
    "플래티넘": "#00d4aa",
    "에메랄드": "#2eccb0",
    "다이아": "#4da6ff",
    "마스터": "#b84dff",
}


def normalize_tier_name(value):
    text = (value or "").strip()
    if text in DEFAULT_TIER_SCORE:
        return text

    if "釉뚮줎" in text:
        return "브론즈"
    if "?ㅻ쾭" in text:
        return "실버"
    if "怨⑤뱶" in text:
        return "골드"
    if "?뚮옒" in text:
        return "플래티넘"
    if "?먮찓" in text:
        return "에메랄드"
    if "?ㅼ씠" in text:
        return "다이아"
    if "留덉뒪" in text:
        return "마스터"
    if "?꾩씠" in text:
        return "아이언"

    return text or "실버"


def normalize_position_name(value):
    text = (value or "").strip()
    if text in POSITION_OPTIONS:
        return text

    if "誘몃뱶" in text:
        return "미드"
    if "?뺢" in text:
        return "정글"
    if "?먮뵜" in text:
        return "원딜"
    if "?쒗뤏" in text:
        return "서포터"
    if "?곴" in text:
        return ANY_POSITION
    if text.startswith("??") or text == "?":
        return "탑"

    return text or ANY_POSITION
