from app.config_loader import cfg_bool, cfg_str
from app.utils import run_cmd_args


def collect_ups_status():
    enabled = cfg_bool("ups", "enabled", default=False)
    target = cfg_str("ups", "target", default="")

    if not enabled or not target:
        return {
            "model": "未配置",
            "battery": None,
        }

    ups_model = ""
    ups_batt = None

    ups_raw = run_cmd_args(["timeout", "1s", "upsc", target], timeout=2)
    if ups_raw:
        for line in ups_raw.splitlines():
            if "Init SSL" in line:
                continue
            if line.startswith(("device.model:", "ups.model:")):
                ups_model = line.split(": ", 1)[-1]
            if line.startswith("battery.charge:"):
                try:
                    ups_batt = int(line.split(": ", 1)[-1])
                except ValueError:
                    pass

    if ups_model or ups_batt is not None:
        return {
            "model": ups_model or "N/A",
            "battery": ups_batt,
        }

    return {
        "model": "通信中断",
        "battery": None,
    }
