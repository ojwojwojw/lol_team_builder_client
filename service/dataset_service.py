import json
import sys
from pathlib import Path

from util.constants import DEFAULT_SERVER_BASE_URL, DEFAULT_TIER_SCORE, normalize_tier_name


if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CONFIG_FILE = DATA_DIR / "config.json"


def _default_config():
    return {
        "tier_score": DEFAULT_TIER_SCORE,
        "server_base_url": DEFAULT_SERVER_BASE_URL,
    }


def _normalize_tier_score(score_map):
    normalized = dict(DEFAULT_TIER_SCORE)

    if not isinstance(score_map, dict):
        return normalized

    for tier, score in score_map.items():
        normalized[normalize_tier_name(tier)] = score

    return normalized


def _save_raw_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def _load_raw_config():
    if not CONFIG_FILE.exists():
        config = _default_config()
        _save_raw_config(config)
        return config

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    config = _default_config()
    if isinstance(data, dict):
        config.update(data)
    config["tier_score"] = _normalize_tier_score(config.get("tier_score"))
    return config


class DatasetService:
    @staticmethod
    def list_files():
        return [
            f.name for f in DATA_DIR.glob("*.json")
            if f.name != "config.json"
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
        if not name.endswith(".json"):
            name += ".json"

        file_path = DATA_DIR / name
        if file_path.exists():
            raise FileExistsError(f"{name} already exists")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([], f)

        return name


def load_config():
    return _load_raw_config().get("tier_score", DEFAULT_TIER_SCORE)


def save_config(score_map):
    config = _load_raw_config()
    config["tier_score"] = _normalize_tier_score(score_map)
    _save_raw_config(config)


def load_server_base_url():
    return _load_raw_config().get("server_base_url", DEFAULT_SERVER_BASE_URL)


def save_server_base_url(base_url):
    config = _load_raw_config()
    config["server_base_url"] = base_url
    _save_raw_config(config)
