import os

from app.config_loader import cfg_str
from app.utils import run_cmd_args


def _expand(path_value, default=""):
    return os.path.expanduser(str(path_value)) if path_value else default


def collect_bluetooth_status():
    bt_mac = cfg_str("bluetooth", "mac", default="")
    bt_default_name = cfg_str("bluetooth", "default_name", default="Bluetooth Speaker")

    bt_info = run_cmd_args(["bluetoothctl", "info", bt_mac], timeout=2) if bt_mac else ""
    bt_connected = "Connected: yes" in bt_info
    bt_paired = bool(bt_info)
    bt_name = ""

    if bt_info:
        for line in bt_info.splitlines():
            if line.strip().startswith("Name:"):
                bt_name = line.split(":", 1)[-1].strip()
                break

    return {
        "paired": bt_paired,
        "connected": bt_connected,
        "name": bt_name or bt_default_name,
    }


def _mpv_get_property(mpv_user: str, mpv_sock: str, prop: str) -> str:
    payload = '{ "command": ["get_property", "' + prop + '"] }\n'
    return run_cmd_args(["sudo", "-u", mpv_user, "socat", "-", mpv_sock], timeout=1.2, input_text=payload)


def collect_mpv_status():
    mpv_sock = _expand(cfg_str("mpv", "socket", default=""))
    mpv_user = cfg_str("mpv", "user", default="")

    mpv_socket_ok = os.path.exists(mpv_sock)
    mpv_playing = False
    mpv_paused = False

    if mpv_socket_ok and mpv_user:
        path_out = _mpv_get_property(mpv_user, mpv_sock, "path")
        has_file = '"data":' in path_out and "null" not in path_out and "unavailable" not in path_out

        if has_file:
            pause_out = _mpv_get_property(mpv_user, mpv_sock, "pause")
            if '"data":true' in pause_out:
                mpv_paused = True
            else:
                mpv_playing = True

    return {
        "socket_ok": mpv_socket_ok,
        "playing": mpv_playing,
        "paused": mpv_paused,
    }


def collect_media_status():
    return {
        "bluetooth": collect_bluetooth_status(),
        "mpv": collect_mpv_status(),
    }
