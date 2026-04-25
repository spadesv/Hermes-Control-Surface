from pathlib import Path
import json
import os

from fastapi import APIRouter

from app.config_loader import cfg

router = APIRouter()

def _expand(path_value, default=""):
    return os.path.expanduser(str(path_value)) if path_value else default

@router.get("/api/cron-jobs")
def get_cron_jobs():
    jobs_file = _expand(cfg("agent", "cron_jobs_file", default="~/.hermes/cron/jobs.json"))
    name_map = cfg("cron_display_names", default={}) or {}

    try:
        with open(Path(jobs_file), encoding="utf-8") as f:
            data = json.load(f)

        jobs = data.get("jobs") or []
        for job in jobs:
            raw_name = str(job.get("name", ""))
            display_name = str(name_map.get(raw_name, raw_name))

            # Keep the real name for future debugging / evolution
            job["raw_name"] = raw_name
            job["display_name"] = display_name

            # Transitional compatibility:
            # current frontend still reads job["name"]
            # so we temporarily expose the display name there
            job["name"] = display_name

        data["jobs"] = jobs
        return data
    except Exception:
        return {"jobs": []}
