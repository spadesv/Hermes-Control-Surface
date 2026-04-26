import re
import time
from pathlib import Path

import psutil

from app.utils import run_cmd_args


def bytes_to_gb(b):
    return round(b / (1024 ** 3), 1)


def seconds_to_dhms(s):
    d = s // 86400
    h = (s % 86400) // 3600
    m = (s % 3600) // 60
    if d > 0:
        return f"{int(d)}d {int(h)}h {int(m)}m"
    return f"{int(h)}h {int(m)}m"


def human_bytes(b):
    b = int(b)
    if b < 1024:
        return f"{b}B"
    elif b < 1048576:
        return f"{b/1024:.1f}KB"
    elif b < 1073741824:
        return f"{b/1048576:.1f}MB"
    return f"{b/1073741824:.1f}GB"


def read_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def _disk_base_device(device: str) -> str:
    """Return the block-device base path for common Linux device names."""
    device = str(device or "")
    if not device.startswith("/dev/"):
        return device

    # /dev/nvme0n1p1 -> /dev/nvme0n1
    # /dev/mmcblk0p1 -> /dev/mmcblk0
    device = re.sub(r"p\d+$", "", device)

    # /dev/sda1 -> /dev/sda, /dev/vda2 -> /dev/vda
    device = re.sub(r"\d+$", "", device)

    return device


def get_disk_parts():
    disk_parts = []
    disk_models = {}

    for block in Path("/sys/block").glob("*"):
        model = read_file(str(block / "device" / "model"))
        if model:
            disk_models[f"/dev/{block.name}"] = model

    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            model = disk_models.get(part.device, "") or disk_models.get(_disk_base_device(part.device), "")
            disk_parts.append({
                "mount": part.mountpoint,
                "device": part.device,
                "model": model,
                "total_gb": bytes_to_gb(usage.total),
                "used_gb": bytes_to_gb(usage.used),
                "percent": usage.percent,
            })
        except OSError:
            # Mount points can disappear, be permission restricted, or be
            # temporarily unavailable. A single bad mount must not break /api/stats.
            pass

    return disk_parts


def get_temps():
    temps = []
    for path in sorted(Path("/sys/class/thermal").glob("thermal_zone*/temp")):
        val = read_file(str(path))
        if val and val.isdigit():
            temps.append(int(val) / 1000)
    return temps


def get_zram():
    z_out = run_cmd_args(["zramctl", "--output", "DISKSIZE,DATA", "--bytes", "--noheadings"], timeout=2)
    z_info = z_out.splitlines()[0] if z_out.splitlines() else ""
    if not z_info:
        return None

    parts = z_info.split()
    if len(parts) == 2 and parts[0].isdigit() and int(parts[0]) > 0:
        z_total = int(parts[0])
        z_used = int(parts[1])
        return {
            "total_human": human_bytes(z_total),
            "used_human": human_bytes(z_used),
            "percent": round(z_used * 100 / z_total, 1),
        }

    return None


def collect_system_metrics():
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_count = psutil.cpu_count()
    load1, load5, load15 = psutil.getloadavg()

    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    uptime_sec = time.time() - psutil.boot_time()

    return {
        "uptime": seconds_to_dhms(uptime_sec),
        "uptime_seconds": int(uptime_sec),
        "cpu": {
            "percent": cpu_percent,
            "cores": cpu_count,
            "load_avg": {
                "1min": round(load1, 2),
                "5min": round(load5, 2),
                "15min": round(load15, 2),
            },
        },
        "memory": {
            "total_gb": bytes_to_gb(mem.total),
            "used_gb": bytes_to_gb(mem.used),
            "available_gb": bytes_to_gb(mem.available),
            "percent": mem.percent,
        },
        "swap": {
            "total_gb": bytes_to_gb(swap.total),
            "used_gb": bytes_to_gb(swap.used),
            "percent": swap.percent,
        },
        "disks": get_disk_parts(),
        "zram": get_zram(),
        "temps": get_temps(),
    }
