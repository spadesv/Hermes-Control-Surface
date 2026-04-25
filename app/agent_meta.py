from pathlib import Path
import json
import os

import yaml

from app.config_loader import cfg, cfg_str
from app.utils import run_cmd_args


def _expand(path_value, default=""):
    return os.path.expanduser(str(path_value)) if path_value else default


def _get_repo_build_meta(repo_path, fallback_file=None):
    commit = "—"
    build_date = "—"

    ok = run_cmd_args(["git", "-C", repo_path, "rev-parse", "--is-inside-work-tree"], timeout=2)
    if ok == "true":
        c = run_cmd_args(["git", "-C", repo_path, "rev-parse", "--short", "HEAD"], timeout=2)
        d = run_cmd_args(["git", "-C", repo_path, "log", "-1", "--format=%cs"], timeout=2)
        if c:
            commit = c
        if d:
            build_date = d

    if build_date == "—" and fallback_file:
        try:
            build_date = Path(fallback_file).stat().st_mtime
            from datetime import datetime
            build_date = datetime.fromtimestamp(build_date).strftime("%Y-%m-%d")
        except Exception:
            pass

    return commit, build_date


def get_agent_meta():
    agent_home = Path(_expand(cfg_str("agent", "home", default="~/.hermes")))
    repo_rel = cfg_str("agent", "repo_relpath", default="hermes-agent")
    pyproject_rel = cfg_str("agent", "pyproject_relpath", default="hermes-agent/pyproject.toml")
    config_rel = cfg_str("agent", "config_relpath", default="config.yaml")
    gateway_state_rel = cfg_str("agent", "gateway_state_relpath", default="gateway_state.json")

    agent_repo = agent_home / repo_rel
    agent_pyproject = agent_home / pyproject_rel
    agent_config = agent_home / config_rel
    agent_gateway_state = agent_home / gateway_state_rel

    agent_version = cfg_str("build", "version", default="0.1.0")
    try:
        with open(agent_pyproject, encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("version = "):
                    agent_version = line.split("=", 1)[-1].strip().strip('"').strip("'")
                    break
    except Exception:
        pass

    agent_commit, agent_build_date = _get_repo_build_meta(str(agent_repo), str(agent_pyproject))
    if agent_commit == "—":
        agent_commit = cfg_str("build", "commit", default="local")
    if agent_build_date == "—":
        agent_build_date = cfg_str("build", "build_date", default="2026-04-25")

    agent_primary_model = "—"
    agent_primary_provider = "—"
    agent_fallback_model = "—"
    agent_fallback_provider = "—"

    try:
        with open(agent_config, encoding="utf-8") as f:
            acfg = yaml.safe_load(f) or {}
        mdl = acfg.get("model") or {}
        agent_primary_model = mdl.get("default", "—")
        agent_primary_provider = mdl.get("provider", "—")
        fb = acfg.get("fallback_providers") or []
        if fb:
            agent_fallback_model = fb[0].get("model", "—")
            agent_fallback_provider = fb[0].get("provider", "—")
    except Exception:
        pass

    agent_gateway_running = False
    agent_platforms = {}

    try:
        with open(agent_gateway_state, encoding="utf-8") as f:
            gs = json.load(f)
        agent_gateway_running = gs.get("gateway_state") == "running"
        for p, info in (gs.get("platforms", {}) or {}).items():
            agent_platforms[p] = info.get("state") == "connected"
    except Exception:
        pass

    return {
        "version": agent_version,
        "build_date": agent_build_date,
        "commit": agent_commit,
        "primary_model": agent_primary_model,
        "primary_provider": agent_primary_provider,
        "fallback_model": agent_fallback_model,
        "fallback_provider": agent_fallback_provider,
        "gateway_running": agent_gateway_running,
        "platforms": agent_platforms,
    }
