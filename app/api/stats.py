import time
from fastapi import APIRouter

from app.agent_meta import get_agent_meta
from app.system_metrics import collect_system_metrics
from app.service_status import collect_service_status, collect_service_status_list
from app.ups_status import collect_ups_status
from app.media_status import collect_media_status
from app.network_status import collect_network_status
from app.system_info import collect_system_info
from app.capabilities import build_capabilities

router = APIRouter()


def _safe_collect(name, fn, fallback):
    """Run one collector without allowing it to break the whole stats API."""
    try:
        value = fn()
        return fallback if value is None else value
    except Exception:
        return fallback


def _default_system_metrics():
    return {
        "uptime": "—",
        "uptime_seconds": 0,
        "cpu": {"load_avg": {}},
        "memory": {},
        "swap": {},
        "disks": [],
        "zram": {},
        "temps": [],
    }


def _default_media_status():
    return {
        "bluetooth": {
            "name": "—",
            "connected": None,
            "paired": None,
        },
        "mpv": {
            "playing": None,
            "paused": None,
            "socket_ok": None,
        },
    }


def _default_system_info():
    return {
        "hostname": "Host",
        "local_ip": "IP",
        "os": "Debian",
    }


def _default_agent_meta():
    return {
        "version": "—",
        "build_date": "—",
        "commit": "—",
        "primary_model": "—",
        "fallback_model": "—",
        "gateway_running": False,
        "platforms": {},
    }


def _default_network_status():
    return {
        "wan_ip": "Offline",
        "proxy_ip": "NONE",
        "gateway_ip": "—",
    }


def _default_capabilities():
    return {
        "sections": {
            "platforms": False,
            "services": False,
            "network": False,
            "storage": True,
            "cpu_temp": True,
            "audio": False,
        },
        "cards": {
            "ups": False,
            "memory": True,
            "disk": True,
        },
        "platforms": {},
        "services": {},
    }


@router.get("/api/stats")
def get_stats():
    system_metrics = _safe_collect("system_metrics", collect_system_metrics, _default_system_metrics())
    media = _safe_collect("media", collect_media_status, _default_media_status())
    system_info = _safe_collect("system_info", collect_system_info, _default_system_info())
    agent_meta = _safe_collect("agent_meta", get_agent_meta, _default_agent_meta())
    services = _safe_collect("services", collect_service_status, {})

    services_list = _safe_collect(
        "services_list",
        lambda: collect_service_status_list(services),
        [],
    )

    capabilities = _safe_collect(
        "capabilities",
        lambda: build_capabilities(agent_meta),
        _default_capabilities(),
    )

    ups = _safe_collect("ups", collect_ups_status, {})
    network = _safe_collect("network", collect_network_status, _default_network_status())

    return {
        "timestamp": int(time.time()),
        "uptime": system_metrics.get("uptime", "—"),
        "uptime_seconds": system_metrics.get("uptime_seconds", 0),
        "cpu": system_metrics.get("cpu", {}),
        "memory": system_metrics.get("memory", {}),
        "swap": system_metrics.get("swap", {}),
        "disks": system_metrics.get("disks", []),
        "zram": system_metrics.get("zram", {}),
        "temps": system_metrics.get("temps", []),
        "ups": ups,
        "network": network,
        "bluetooth": media.get("bluetooth", {}),
        "mpv": media.get("mpv", {}),
        "services": services,
        "services_list": services_list,
        "system": system_info,
        "hostname": system_info.get("hostname", "Host"),
        "local_ip": system_info.get("local_ip", "IP"),
        "agent": agent_meta,
        "capabilities": capabilities,
    }
