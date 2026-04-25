import re
import time

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


def get_disk_parts():
    disk_parts = []
    disk_models = {}

    for i in range(10):
        dev = f"sd{chr(97+i)}"
        model_path = f"/sys/block/{dev}/device/model"
        try:
            with open(model_path, encoding="utf-8") as f:
                disk_models[f"/dev/{dev}"] = f.read().strip()
        except FileNotFoundError:
            pass

    for p in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(p.mountpoint)
            model = disk_models.get(p.device, "")
            if not model:
                base = re.sub(r"\d+$", "", p.device)
                model = disk_models.get(base, "")
            disk_parts.append({
                "mount": p.mountpoint,
                "device": p.device,
                "model": model,
                "total_gb": bytes_to_gb(usage.total),
                "used_gb": bytes_to_gb(usage.used),
                "percent": usage.percent,
            })
        except PermissionError:
            pass

    return disk_parts


def get_temps():
    temps = []
    for i in range(10):
        val = read_file(f"/sys/class/thermal/thermal_zone{i}/temp")
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
