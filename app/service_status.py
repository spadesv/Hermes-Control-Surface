import os

from app.config_loader import cfg_nonempty, cfg_str
from app.utils import run_cmd_args


def check_svc(name):
    name = str(name or "").strip()
    if not name:
        return False
    return run_cmd_args(["systemctl", "is-active", name], timeout=2) == "active"


def _mpv_user_runtime_env(mpv_user: str) -> list[str]:
    """Build a safe user-session environment for systemctl --user.

    For the public package, the runtime directory is either configured
    explicitly or derived
    from the configured mpv user with `id -u`.
    """
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


def collect_service_status():
    mpv_user = cfg_str("mpv", "user", default="")
    pipewire_user_unit = cfg_str("services", "pipewire_user", default="bt-music.service")

    pipewire_user_active = False
    if mpv_user and pipewire_user_unit:
        cmd = ["sudo", "-u", mpv_user, "env"]
        cmd.extend(_mpv_user_runtime_env(mpv_user))
        cmd.extend(["systemctl", "--user", "is-active", pipewire_user_unit])
        pipewire_user_active = bool(run_cmd_args(cmd, timeout=2))

    return {
        "hermes": check_svc(cfg_nonempty("services", "hermes", default="hermes-gateway")) or bool(run_cmd_args(["pgrep", "-fi", "hermes"], timeout=2)),
        "crowdsec": check_svc(cfg_nonempty("services", "crowdsec", default="crowdsec")),
        "docker": check_svc(cfg_nonempty("services", "docker", default="docker")),
        "watchdog": check_svc(cfg_nonempty("services", "watchdog", default="watchdog")) or os.path.exists("/dev/watchdog0") or os.path.exists("/dev/watchdog"),
        "smb": check_svc(cfg_nonempty("services", "smb", default="smbd")),
        "pipewire": check_svc(cfg_nonempty("services", "pipewire_system", default="bt-music.service")) or pipewire_user_active,
    }
