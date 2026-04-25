import time
import psutil

from app.config_loader import cfg_bool, cfg_int, cfg_str
from app.utils import extract_ipv4, run_cmd_args, run_shell_cmd

_CACHE = {
    "wan_ip": "Offline",
    "proxy_ip": "NONE",
    "ts": 0.0,
}


def _probe_ip(url: str) -> str:
    if not url:
        return ""
    out = run_cmd_args(
        ["curl", "-4", "-s", "--connect-timeout", "2", "--max-time", "4", url],
        timeout=5,
    )
    return extract_ipv4(out)


def _probe_command(cmd: str) -> str:
    # command_wan / command_proxy are trusted local administrator commands.
    if not cmd:
        return ""
    return extract_ipv4(run_shell_cmd(cmd, timeout=5))


def collect_network_status():
    net = psutil.net_io_counters()
    bytes_sent = getattr(net, "bytes_sent", 0) if net is not None else 0
    bytes_recv = getattr(net, "bytes_recv", 0) if net is not None else 0
    enabled = cfg_bool("network", "enabled", default=True)
    gateway_ip = cfg_str("network", "gateway_ip", default="—")

    if not enabled:
        return {
            "bytes_sent": bytes_sent,
            "bytes_recv": bytes_recv,
            "wan_ip": "Offline",
            "proxy_ip": "NONE",
            "gateway_ip": gateway_ip,
        }

    provider = cfg_str("network", "provider", default="dual_http_probe")
    cache_seconds = cfg_int("network", "cache_seconds", default=300, min_value=5, max_value=86400)

    now = time.time()
    if now - _CACHE["ts"] >= cache_seconds:
        wan_ip = "Offline"
        proxy_ip = "NONE"

        if provider == "dual_http_probe":
            wan_ip = _probe_ip(cfg_str("network", "direct_probe_url", default="")) or "Offline"
            proxy_ip = _probe_ip(cfg_str("network", "proxy_probe_url", default="")) or "NONE"

        elif provider == "command":
            wan_ip = _probe_command(cfg_str("network", "command_wan", default="")) or "Offline"
            proxy_ip = _probe_command(cfg_str("network", "command_proxy", default="")) or "NONE"

        elif provider == "manual":
            wan_ip = cfg_str("network", "manual_wan", default="Offline")
            proxy_ip = cfg_str("network", "manual_proxy", default="NONE")

        if proxy_ip == wan_ip:
            proxy_ip = "NONE"

        _CACHE["wan_ip"] = wan_ip
        _CACHE["proxy_ip"] = proxy_ip
        _CACHE["ts"] = now

    return {
        "bytes_sent": bytes_sent,
        "bytes_recv": bytes_recv,
        "wan_ip": _CACHE["wan_ip"],
        "proxy_ip": _CACHE["proxy_ip"],
        "gateway_ip": gateway_ip,
    }
