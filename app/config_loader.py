from __future__ import annotations

from pathlib import Path
from threading import RLock
from time import time
from typing import Any

import yaml


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_PATH = CONFIG_DIR / "config.yaml"
EXAMPLE_CONFIG_PATH = CONFIG_DIR / "config.example.yaml"

_LOCK = RLock()

_CONFIG_CACHE: dict[str, Any] | None = None
_CONFIG_SOURCE: str | None = None
_CONFIG_MTIME_NS: int | None = None
_CONFIG_LOADED_AT: float | None = None
_CONFIG_ERROR: str | None = None

_TRUE_VALUES = {"1", "true", "yes", "y", "on", "enable", "enabled"}
_FALSE_VALUES = {"0", "false", "no", "n", "off", "disable", "disabled", "none", "null", ""}


def _select_config_path() -> Path:
    if CONFIG_PATH.exists():
        return CONFIG_PATH
    return EXAMPLE_CONFIG_PATH


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")

    return data


def _load_from_path(path: Path) -> tuple[dict[str, Any], int]:
    stat = path.stat()
    return _read_yaml(path), stat.st_mtime_ns


def load_config(force_reload: bool = False) -> dict[str, Any]:
    """
    Load runtime configuration with mtime-based hot reload.

    Behavior:
    - config/config.yaml is preferred when present.
    - config/config.example.yaml is used as fallback when config.yaml is missing.
    - If the active config changes on disk, it is reloaded automatically.
    - If a reload fails, the last-known-good config remains active.
    """

    global _CONFIG_CACHE, _CONFIG_SOURCE, _CONFIG_MTIME_NS, _CONFIG_LOADED_AT, _CONFIG_ERROR

    with _LOCK:
        path = _select_config_path()

        try:
            current_mtime_ns = path.stat().st_mtime_ns
        except FileNotFoundError as exc:
            _CONFIG_ERROR = f"config file not found: {exc}"
            return _CONFIG_CACHE or {}

        same_file = _CONFIG_SOURCE == str(path)
        same_mtime = _CONFIG_MTIME_NS == current_mtime_ns

        if (
            _CONFIG_CACHE is not None
            and not force_reload
            and same_file
            and same_mtime
        ):
            return _CONFIG_CACHE

        try:
            data, mtime_ns = _load_from_path(path)
        except Exception as exc:
            _CONFIG_ERROR = f"failed to load {path}: {exc}"

            if _CONFIG_CACHE is not None:
                return _CONFIG_CACHE

            if path != EXAMPLE_CONFIG_PATH and EXAMPLE_CONFIG_PATH.exists():
                try:
                    data, mtime_ns = _load_from_path(EXAMPLE_CONFIG_PATH)
                    _CONFIG_CACHE = data
                    _CONFIG_SOURCE = str(EXAMPLE_CONFIG_PATH)
                    _CONFIG_MTIME_NS = mtime_ns
                    _CONFIG_LOADED_AT = time()
                    _CONFIG_ERROR = f"using example config after primary load failure: {exc}"
                    return _CONFIG_CACHE
                except Exception as fallback_exc:
                    _CONFIG_ERROR = (
                        f"failed to load primary config {path}: {exc}; "
                        f"failed to load example config {EXAMPLE_CONFIG_PATH}: {fallback_exc}"
                    )

            return {}

        _CONFIG_CACHE = data
        _CONFIG_SOURCE = str(path)
        _CONFIG_MTIME_NS = mtime_ns
        _CONFIG_LOADED_AT = time()
        _CONFIG_ERROR = None
        return _CONFIG_CACHE


def reload_config() -> dict[str, Any]:
    return load_config(force_reload=True)


def get_config_status() -> dict[str, Any]:
    load_config()
    return {
        "source": _CONFIG_SOURCE,
        "mtime_ns": _CONFIG_MTIME_NS,
        "loaded_at": _CONFIG_LOADED_AT,
        "error": _CONFIG_ERROR,
        "hot_reload": True,
    }


def cfg(*keys: str, default: Any = None) -> Any:
    data: Any = load_config()

    for key in keys:
        if not isinstance(data, dict):
            return default
        if key not in data:
            return default
        data = data[key]

    return default if data is None else data



def cfg_section(*keys: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a config subsection as a dict.

    This keeps modules from re-reading YAML with process-dependent paths.
    """
    value = cfg(*keys, default=default or {})
    return value if isinstance(value, dict) else (default or {})


def cfg_str(*keys: str, default: str = "", strip: bool = True) -> str:
    value = cfg(*keys, default=default)
    if value is None:
        return default
    text = str(value)
    return text.strip() if strip else text


def cfg_nonempty(*keys: str, default: str = "") -> str:
    value = cfg_str(*keys, default=default, strip=True)
    return value if value else ""


def cfg_bool(*keys: str, default: bool = False) -> bool:
    value = cfg(*keys, default=default)

    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in _TRUE_VALUES:
            return True
        if normalized in _FALSE_VALUES:
            return False

    return default


def cfg_int(*keys: str, default: int = 0, min_value: int | None = None, max_value: int | None = None) -> int:
    value = cfg(*keys, default=default)

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default

    if min_value is not None and parsed < min_value:
        parsed = min_value
    if max_value is not None and parsed > max_value:
        parsed = max_value

    return parsed
