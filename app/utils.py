import re
import subprocess
from collections.abc import Sequence


def run_shell_cmd(cmd: str, timeout=3) -> str:
    """
    Run a trusted local shell command.

    Use this only for commands intentionally configured by the local administrator,
    such as network.command_wan / network.command_proxy. For normal system calls,
    prefer run_cmd_args() so YAML values are passed as arguments instead of being
    interpolated into a shell string.
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def run_cmd(cmd: str, timeout=3) -> str:
    """Backward-compatible alias for trusted local shell commands."""
    return run_shell_cmd(cmd, timeout=timeout)


def run_cmd_args(args: Sequence[str], timeout=3, input_text: str | None = None) -> str:
    """Run a command without invoking a shell."""
    try:
        result = subprocess.run(
            [str(a) for a in args],
            shell=False,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def extract_ipv4(text):
    m = re.search(r'(\d+\.\d+\.\d+\.\d+)', text or "")
    return m.group(1) if m else ""
