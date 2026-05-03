import json
import sys
from pathlib import Path

from domain.constants import (
    DEFAULT_BUILD_WEIGHTS,
    DEFAULT_SERVER_BASE_URL,
    DEFAULT_THEME_MODE,
    DEFAULT_TIER_SCORE,
    normalize_theme_mode,
    normalize_tier_name,
)


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
        "build_weights": DEFAULT_BUILD_WEIGHTS,
        "server_base_url": DEFAULT_SERVER_BASE_URL,
        "theme_mode": DEFAULT_THEME_MODE,
        "auth_token": "",
        "auth_username": "",
    }


def _normalize_tier_score(score_map):
    normalized = dict(DEFAULT_TIER_SCORE)

    if not isinstance(score_map, dict):
        return normalized

    for tier, score in score_map.items():
        normalized[normalize_tier_name(tier)] = score

    return normalized


def _save_raw_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=2, ensure_ascii=False)


def _load_raw_config():
    if not CONFIG_FILE.exists():
        config = _default_config()
        _save_raw_config(config)
        return config

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        data = {}

    config = _default_config()
    if isinstance(data, dict):
        config.update(data)

    config["tier_score"] = _normalize_tier_score(config.get("tier_score"))
    config["build_weights"] = _normalize_build_weights(config.get("build_weights"))
    config["theme_mode"] = normalize_theme_mode(config.get("theme_mode"))
    return config


def _normalize_build_weights(weight_map):
    normalized = dict(DEFAULT_BUILD_WEIGHTS)

    if not isinstance(weight_map, dict):
        return normalized

    for key, default_value in DEFAULT_BUILD_WEIGHTS.items():
        value = weight_map.get(key, default_value)
        try:
            normalized[key] = int(value)
        except Exception:
            normalized[key] = default_value

    return normalized


class DatasetRepository:
    @staticmethod
    def list_files():
        return [
            file.name
            for file in DATA_DIR.glob("*.json")
            if file.name != "config.json"
        ]

    @staticmethod
    def load(file_name):
        file_path = DATA_DIR / file_name
        if not file_path.exists():
            return []

        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def save(file_name, users):
        file_path = DATA_DIR / file_name
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(users, file, indent=2, ensure_ascii=False)

    @staticmethod
    def create(name):
        if not name.endswith(".json"):
            name += ".json"

        file_path = DATA_DIR / name
        if file_path.exists():
            raise FileExistsError(f"{name} already exists")

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump([], file)

        return name

    @staticmethod
    def delete(file_name):
        file_path = DATA_DIR / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"{file_name} does not exist")

        file_path.unlink()


def load_config():
    return _load_raw_config().get("tier_score", DEFAULT_TIER_SCORE)


def save_config(score_map):
    config = _load_raw_config()
    config["tier_score"] = _normalize_tier_score(score_map)
    _save_raw_config(config)


def load_build_weights():
    return _load_raw_config().get("build_weights", DEFAULT_BUILD_WEIGHTS)


def save_build_weights(weight_map):
    config = _load_raw_config()
    config["build_weights"] = _normalize_build_weights(weight_map)
    _save_raw_config(config)


def load_server_base_url():
    return _load_raw_config().get("server_base_url", DEFAULT_SERVER_BASE_URL)


def save_server_base_url(base_url):
    config = _load_raw_config()
    config["server_base_url"] = base_url
    _save_raw_config(config)


def load_auth_token():
    return str(_load_raw_config().get("auth_token", "") or "")


def save_auth_token(token):
    config = _load_raw_config()
    config["auth_token"] = str(token or "").strip()
    _save_raw_config(config)


def clear_auth_token():
    config = _load_raw_config()
    config["auth_token"] = ""
    _save_raw_config(config)


def load_auth_username():
    return str(_load_raw_config().get("auth_username", "") or "")


def save_auth_username(username):
    config = _load_raw_config()
    config["auth_username"] = str(username or "").strip()
    _save_raw_config(config)


def load_theme_mode():
    return _load_raw_config().get("theme_mode", DEFAULT_THEME_MODE)


def save_theme_mode(theme_mode):
    config = _load_raw_config()
    config["theme_mode"] = normalize_theme_mode(theme_mode)
    _save_raw_config(config)


def save_dataset(file_name, users):
    DatasetRepository.save(file_name, users)
