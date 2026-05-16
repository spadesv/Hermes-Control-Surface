from fastapi import APIRouter

from app.config_loader import cfg_str

router = APIRouter()


@router.get("/build-meta.json")
def build_meta():
    build_date = cfg_str("build", "build_date", default="2026-05-16")
    return {
        "version": cfg_str("build", "version", default="0.1.3"),
        "build_date": build_date,
        "buildDate": build_date,
        "commit": cfg_str("build", "commit", default="v0.1.3"),
        "channel": cfg_str("build", "channel", default="stable"),
    }
