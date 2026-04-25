from fastapi import APIRouter

from app.config_loader import cfg_str

router = APIRouter()


@router.get("/api/public-config")
def get_public_config():
    return {
        "page_title": cfg_str("site", "page_title", default="Hermes Dashboard"),
        "badge_os": cfg_str("frontend", "badge_os", default=""),
        "badge_host": cfg_str("frontend", "badge_host", default=""),
        "badge_ip": cfg_str("frontend", "badge_ip", default=""),
        "brand_eyebrow_desktop": cfg_str("frontend", "brand_eyebrow_desktop", default="Hermes Agent"),
        "brand_title_desktop": cfg_str("frontend", "brand_title_desktop", default="Dashboard"),
        "brand_eyebrow_mobile": cfg_str("frontend", "brand_eyebrow_mobile", default="HERMES AGENT"),
        "brand_title_mobile": cfg_str("frontend", "brand_title_mobile", default="Dashboard"),
        "footer_brand": cfg_str("frontend", "footer_brand", default="Hermes Agent"),
    }
