import socket

from app.config_loader import cfg_nonempty, cfg_str
from app.utils import run_cmd_args


def _detect_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return ""


def _detect_os_version():
    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[-1].strip().strip('"').replace("GNU/Linux ", "")
    except Exception:
        pass
    return ""


def _detect_cpu_model():
    out = run_cmd_args(["lscpu"], timeout=2)
    for line in out.splitlines():
        if line.startswith("Model name:"):
            return line.split(":", 1)[-1].strip()
    return ""


def collect_system_info():
    badge_os = cfg_nonempty("frontend", "badge_os", default="")
    badge_host = cfg_nonempty("frontend", "badge_host", default="")
    badge_ip = cfg_nonempty("frontend", "badge_ip", default="")

    os_version = badge_os or _detect_os_version() or "Linux"
    hostname = badge_host or socket.gethostname()
    local_ip = badge_ip or _detect_local_ip() or "IP"

    kernel = run_cmd_args(["uname", "-r"], timeout=2)
    cpu_model = _detect_cpu_model() or cfg_str("system", "cpu_model_fallback", default="Unknown CPU")

    return {
        "os": os_version,
        "kernel": kernel or "—",
        "cpu_model": cpu_model or "Unknown CPU",
        "hostname": hostname,
        "local_ip": local_ip,
    }
