import time
from fastapi import APIRouter

from app.agent_meta import get_agent_meta
from app.system_metrics import collect_system_metrics
from app.service_status import collect_service_status, collect_service_status_list
from app.ups_status import collect_ups_status
from app.media_status import collect_media_status
from app.network_status import collect_network_status
from app.system_info import collect_system_info
from app.capabilities import build_capabilities

router = APIRouter()

@router.get("/api/stats")
def get_stats():
    system_metrics = collect_system_metrics()
    media = collect_media_status()
    system_info = collect_system_info()
    agent_meta = get_agent_meta()
    services = collect_service_status()

    return {
        "timestamp": int(time.time()),
        "uptime": system_metrics["uptime"],
        "uptime_seconds": system_metrics["uptime_seconds"],
        "cpu": system_metrics["cpu"],
        "memory": system_metrics["memory"],
        "swap": system_metrics["swap"],
        "disks": system_metrics["disks"],
        "zram": system_metrics["zram"],
        "temps": system_metrics["temps"],
        "ups": collect_ups_status(),
        "network": collect_network_status(),
        "bluetooth": media["bluetooth"],
        "mpv": media["mpv"],
        "services": services,
        "services_list": collect_service_status_list(services),
        "system": system_info,
        "hostname": system_info["hostname"],
        "local_ip": system_info["local_ip"],
        "agent": agent_meta,
        "capabilities": build_capabilities(agent_meta),
    }
