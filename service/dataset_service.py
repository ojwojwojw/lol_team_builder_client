import json
import sys
from pathlib import Path
from util.constants import DEFAULT_TIER_SCORE

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CONFIG_FILE = DATA_DIR / "config.json"

class DatasetService:

    @staticmethod
    def list_files():
        return [
            f.name for f in DATA_DIR.glob("*.json")
            if f.name != "config.json"   # 🔥 핵심
        ]

    @staticmethod
    def load(file_name):
        file_path = DATA_DIR / file_name
        if not file_path.exists():
            return []

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save(file_name, users):
        file_path = DATA_DIR / file_name
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)

    @staticmethod
    def create(name):
        # 🔥 확장자 강제
        if not name.endswith(".json"):
            name += ".json"

        file_path = DATA_DIR / name

        # 🔥 중복 방지
        if file_path.exists():
            raise FileExistsError(f"{name} 이미 존재")

        # 🔥 생성
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([], f)

        return name  # 🔥 생성된 파일명 반환
    

    CONFIG_FILE = DATA_DIR / "config.json"


def load_config():
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_TIER_SCORE)
        return DEFAULT_TIER_SCORE

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)["tier_score"]
    except:
        return DEFAULT_TIER_SCORE


def save_config(score_map):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"tier_score": score_map}, f, indent=2, ensure_ascii=False)