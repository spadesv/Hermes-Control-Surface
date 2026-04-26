import os
from pathlib import Path

import yaml

from app.config_loader import cfg_nonempty, cfg_str
from app.utils import run_cmd_args


KNOWN_SERVICE_ORDER = ["hermes", "docker", "crowdsec", "pipewire", "smb", "watchdog"]
SPECIAL_SERVICE_KEYS = {"pipewire_system", "pipewire_user"}

SERVICE_LABELS = {
    "hermes": "Hermes Agent",
    "docker": "Docker",
    "crowdsec": "CrowdSec",
    "pipewire": "PipeWire",
    "smb": "SMB",
    "watchdog": "Watchdog",
}

SERVICE_DEFAULT_UNITS = {
    "hermes": "hermes-gateway",
    "docker": "docker",
    "crowdsec": "crowdsec",
    "smb": "smbd",
    "watchdog": "watchdog",
}


def check_svc(name):
    name = str(name or "").strip()
    if not name:
        return False
    return run_cmd_args(["systemctl", "is-active", name], timeout=2) == "active"


def _load_yaml_config() -> dict:
    """Load runtime config so service keys can be enumerated dynamically.

    The dashboard still uses cfg_* helpers for individual values. This raw read
    only solves the old hardcoded-service-list problem.
    """
    for path in (Path.cwd() / "config" / "config.yaml", Path.cwd() / "config" / "config.example.yaml"):
        try:
            if path.exists():
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def _config_section(name: str) -> dict:
    section = (_load_yaml_config().get(name) or {})
    return section if isinstance(section, dict) else {}


def _raw_services_config() -> dict:
    return _config_section("services")


def _clean_unit(value) -> str:
    return str(value or "").strip()


def _humanize_service_key(key: str) -> str:
    key = str(key or "").strip()
    if not key:
        return "Service"

    normalized = key.replace("_", " ").replace("-", " ").strip()
    if not normalized:
        return key

    upper_words = {"api", "cpu", "dns", "gpu", "ha", "http", "https", "ip", "mpv", "smb", "ssh", "ssl", "ups", "vpn"}
    words = []
    for word in normalized.split():
        low = word.lower()
        if low in upper_words:
            words.append(low.upper())
        elif low == "nginx":
            words.append("Nginx")
        elif low == "redis":
            words.append("Redis")
        elif low == "docker":
            words.append("Docker")
        elif low == "crowdsec":
            words.append("CrowdSec")
        elif low == "homeassistant":
            words.append("Home Assistant")
        else:
            words.append(word[:1].upper() + word[1:])
    return " ".join(words)


def _service_label(key: str) -> str:
    labels = _config_section("service_labels")
    label = labels.get(key)
    if isinstance(label, str) and label.strip():
        return label.strip()
    return SERVICE_LABELS.get(key, _humanize_service_key(key))


def get_service_specs() -> list[dict]:
    """Return service definitions in display order.

    Compatibility rules:
    - Existing `services:` dict remains supported.
    - Known services keep stable labels and order.
    - pipewire_system + pipewire_user are merged into one logical PipeWire row.
    - Extra user-defined service keys under `services:` are appended dynamically.
    """
    raw_services = _raw_services_config()
    specs = []
    seen = set()

    for key in KNOWN_SERVICE_ORDER:
        if key == "pipewire":
            pipewire_system = cfg_nonempty("services", "pipewire_system", default="")
            pipewire_user = cfg_nonempty("services", "pipewire_user", default="")
            pipewire_plain = cfg_nonempty("services", "pipewire", default="")
            configured = bool(pipewire_system or pipewire_user or pipewire_plain)
            unit = pipewire_plain or pipewire_system or pipewire_user or ""
        else:
            default_unit = SERVICE_DEFAULT_UNITS.get(key, "")
            configured_raw = _clean_unit(raw_services.get(key, ""))
            configured = bool(configured_raw)
            unit = cfg_nonempty("services", key, default=default_unit)

        specs.append({
            "key": key,
            "label": _service_label(key),
            "unit": _clean_unit(unit),
            "configured": configured,
        })
        seen.add(key)

    for key, value in raw_services.items():
        key = str(key or "").strip()
        if not key or key in seen or key in SPECIAL_SERVICE_KEYS:
            continue

        unit = _clean_unit(value)
        if not unit:
            continue

        specs.append({
            "key": key,
            "label": _service_label(key),
            "unit": unit,
            "configured": True,
        })
        seen.add(key)

    return specs


def _mpv_user_runtime_env(mpv_user: str) -> list[str]:
    """Build a safe user-session environment for systemctl --user."""
    mpv_user = str(mpv_user or "").strip()
    runtime_dir = cfg_str("mpv", "runtime_dir", default="")
    bus_address = cfg_str("mpv", "dbus_session_bus_address", default="")

    if not runtime_dir and mpv_user:
        uid = run_cmd_args(["id", "-u", mpv_user], timeout=1)
        if uid.isdigit():
            runtime_dir = f"/run/user/{uid}"

    if not bus_address and runtime_dir:
        bus_address = f"unix:path={runtime_dir}/bus"

    env = []
    if runtime_dir:
        env.append(f"XDG_RUNTIME_DIR={runtime_dir}")
    if bus_address:
        env.append(f"DBUS_SESSION_BUS_ADDRESS={bus_address}")
    return env


def _pipewire_running() -> bool:
    mpv_user = cfg_str("mpv", "user", default="")
    pipewire_user_unit = cfg_str("services", "pipewire_user", default="")
    pipewire_system_unit = cfg_nonempty("services", "pipewire", default="") or cfg_nonempty(
        "services", "pipewire_system", default=""
    )

    pipewire_user_active = False
    if mpv_user and pipewire_user_unit:
        cmd = ["sudo", "-u", mpv_user, "env"]
        cmd.extend(_mpv_user_runtime_env(mpv_user))
        cmd.extend(["systemctl", "--user", "is-active", pipewire_user_unit])
        pipewire_user_active = bool(run_cmd_args(cmd, timeout=2))

    return check_svc(pipewire_system_unit) or pipewire_user_active


def _service_running(spec: dict) -> bool:
    key = spec.get("key")
    unit = spec.get("unit")

    if key == "pipewire":
        return _pipewire_running()

    if key == "hermes":
        return check_svc(unit) or bool(run_cmd_args(["pgrep", "-fi", "hermes"], timeout=2))

    if key == "watchdog":
        return check_svc(unit) or os.path.exists("/dev/watchdog0") or os.path.exists("/dev/watchdog")

    return check_svc(unit)


def collect_service_status():
    """Return the legacy service status mapping: {key: running_bool}."""
    return {spec["key"]: _service_running(spec) for spec in get_service_specs()}


def collect_service_status_list(statuses=None):
    """Return a dynamic service list for frontend rendering."""
    statuses = statuses if isinstance(statuses, dict) else collect_service_status()
    rows = []

    for spec in get_service_specs():
        key = spec["key"]
        rows.append({
            "key": key,
            "label": spec.get("label") or _humanize_service_key(key),
            "unit": spec.get("unit") or "",
            "configured": bool(spec.get("configured")),
            "running": statuses.get(key),
        })

    return rows
