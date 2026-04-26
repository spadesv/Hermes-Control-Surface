from app.config_loader import cfg_bool, cfg_nonempty, cfg_section, cfg_str
from app.service_status import get_service_specs


VALID_POLICY = {"auto", "show", "hide"}

KNOWN_PLATFORM_ORDER = ["telegram", "discord", "homeassistant"]


def _policy(*keys, default="auto"):
    value = cfg_str(*keys, default=default).lower()
    return value if value in VALID_POLICY else default


def _resolve(policy, auto_value):
    if policy == "show":
        return True
    if policy == "hide":
        return False
    return bool(auto_value)


def _dashboard_subsection(name: str) -> dict:
    dashboard = cfg_section("dashboard", default={})
    section = dashboard.get(name) or {}
    return section if isinstance(section, dict) else {}


def _append_unique(keys: list[str], value) -> None:
    key = str(value or "").strip()
    if key and key not in keys:
        keys.append(key)


def _build_platform_capabilities(agent_meta=None):
    agent_platforms = (agent_meta or {}).get("platforms") or {}
    if not isinstance(agent_platforms, dict):
        agent_platforms = {}

    configured_platforms = _dashboard_subsection("platforms")

    keys = []
    for key in KNOWN_PLATFORM_ORDER:
        _append_unique(keys, key)
    for key in configured_platforms.keys():
        _append_unique(keys, key)
    for key in agent_platforms.keys():
        _append_unique(keys, key)

    platforms = {}
    for key in keys:
        platforms[key] = _resolve(
            _policy("dashboard", "platforms", key),
            key in agent_platforms,
        )

    return platforms


def _build_service_capabilities():
    services = {}

    for spec in get_service_specs():
        key = spec["key"]
        default_policy = "show" if key == "hermes" else "auto"
        services[key] = _resolve(
            _policy("dashboard", "services", key, default=default_policy),
            bool(spec.get("configured")),
        )

    return services


def build_capabilities(agent_meta=None):
    """
    Build dashboard display capabilities.

    Policy values:
    - auto: show when related config/data exists
    - show: force show
    - hide: force hide

    Collectors answer "what is the current data?"
    Capabilities answer "should the dashboard show this block?"
    """

    ups_auto = cfg_bool("ups", "enabled", default=False) and bool(cfg_nonempty("ups", "target", default=""))
    network_auto = cfg_bool("network", "enabled", default=False)

    bluetooth_auto = bool(cfg_nonempty("bluetooth", "mac", default=""))
    mpv_auto = bool(cfg_nonempty("mpv", "socket", default="")) and bool(cfg_nonempty("mpv", "user", default=""))
    audio_auto = bluetooth_auto or mpv_auto

    platforms = _build_platform_capabilities(agent_meta)
    services = _build_service_capabilities()

    sections = {
        "platforms": _resolve(_policy("dashboard", "sections", "platforms"), any(platforms.values())),
        "services": _resolve(_policy("dashboard", "sections", "services"), any(services.values())),
        "network": _resolve(_policy("dashboard", "sections", "network"), network_auto),
        "storage": _resolve(_policy("dashboard", "sections", "storage", default="show"), True),
        "cpu_temp": _resolve(_policy("dashboard", "sections", "cpu_temp", default="show"), True),
        "audio": _resolve(_policy("dashboard", "sections", "audio"), audio_auto),
    }

    cards = {
        "ups": _resolve(_policy("dashboard", "cards", "ups"), ups_auto),
        "memory": _resolve(_policy("dashboard", "cards", "memory", default="show"), True),
        "disk": _resolve(_policy("dashboard", "cards", "disk", default="show"), True),
    }

    return {
        "sections": sections,
        "cards": cards,
        "platforms": platforms,
        "services": services,
    }
