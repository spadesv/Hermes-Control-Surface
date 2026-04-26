from fastapi import APIRouter

from app.agent_meta import get_agent_meta
from app.config_loader import cfg_str

router = APIRouter()

@router.get("/build-meta.json")
def build_meta():
    agent = get_agent_meta()
    build_date = agent.get("build_date") or cfg_str("build", "build_date", default="2026-04-26")
    return {
        "version": agent.get("version") or cfg_str("build", "version", default="0.1.1"),
        "build_date": build_date,
        "buildDate": build_date,
        "commit": agent.get("commit") or cfg_str("build", "commit", default="v0.1.1"),
        "channel": cfg_str("build", "channel", default="release"),
    }
