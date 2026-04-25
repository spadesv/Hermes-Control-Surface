from html import escape
from pathlib import Path
import re

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse

from app.api.public_config import router as public_config_router
from app.api.stats import router as stats_router
from app.api.cron import router as cron_router
from app.api.build_meta import router as build_meta_router
from app.config_loader import cfg_str

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

LANG_COOKIE = "hcs_lang"
SUPPORTED_LANGS = {
    "en": STATIC_DIR / "index.en.html",
    "zh-CN": STATIC_DIR / "index.zh-CN.html",
}

app = FastAPI(title="Hermes Control Surface")

# The frontend is served by the same FastAPI app, so CORS is intentionally not
# opened by default. Keep it same-origin unless you explicitly place a separate
# trusted frontend behind your own reverse proxy.

app.include_router(public_config_router)
app.include_router(stats_router)
app.include_router(cron_router)
app.include_router(build_meta_router)


def _preferred_lang_from_accept_language(request: Request) -> str:
    """Return the best supported language from the browser Accept-Language header.

    The dashboard currently supports English and Simplified Chinese. This parser
    respects both q weights and header order, so a low-priority zh entry will not
    override a higher-priority English preference.
    """
    header = request.headers.get("accept-language") or ""
    best_lang = "en"
    best_q = -1.0
    best_order = 10_000

    for order, part in enumerate(header.split(",")):
        part = part.strip()
        if not part:
            continue

        pieces = [p.strip() for p in part.split(";") if p.strip()]
        tag = pieces[0].lower()
        q = 1.0

        for piece in pieces[1:]:
            if piece.lower().startswith("q="):
                try:
                    q = float(piece.split("=", 1)[1])
                except ValueError:
                    q = 0.0

        if q <= 0:
            continue

        if tag == "zh" or tag.startswith("zh-"):
            candidate = "zh-CN"
        elif tag == "en" or tag.startswith("en-") or tag == "*":
            candidate = "en"
        else:
            continue

        if q > best_q or (q == best_q and order < best_order):
            best_lang = candidate
            best_q = q
            best_order = order

    return best_lang


def _resolve_lang(request: Request) -> tuple[str, str | None]:
    q = request.query_params.get("lang")
    if q in SUPPORTED_LANGS:
        return q, q
    if q == "system":
        return _preferred_lang_from_accept_language(request), "system"

    cookie_lang = request.cookies.get(LANG_COOKIE)
    if cookie_lang in SUPPORTED_LANGS:
        return cookie_lang, None

    return _preferred_lang_from_accept_language(request), None


def _replace_first(html: str, pattern: str, replacement: str) -> str:
    return re.sub(pattern, replacement, html, count=1, flags=re.S)


def _render_index_html(lang: str) -> str:
    src = SUPPORTED_LANGS.get(lang, SUPPORTED_LANGS["en"])
    html = src.read_text(encoding="utf-8")

    page_title = cfg_str("site", "page_title", default="Hermes Dashboard")
    brand_desktop = cfg_str("frontend", "brand_title_desktop", default="Dashboard")
    brand_mobile = cfg_str("frontend", "brand_title_mobile", default="Dashboard")

    html = _replace_first(
        html,
        r"<title>.*?</title>",
        f"<title>{escape(page_title)}</title>",
    )
    html = _replace_first(
        html,
        r'<strong id="brandTitleDesktop">.*?</strong>',
        f'<strong id="brandTitleDesktop">{escape(brand_desktop)}</strong>',
    )
    html = _replace_first(
        html,
        r'<strong id="brandTitleMobile" class="m-brand__title">.*?</strong>',
        f'<strong id="brandTitleMobile" class="m-brand__title">{escape(brand_mobile)}</strong>',
    )
    html = _replace_first(
        html,
        r'<html lang="[^"]+">',
        f'<html lang="{lang}">',
    )
    return html



@app.head("/")
def root_index_head(request: Request):
    lang, cookie_action = _resolve_lang(request)
    resp = HTMLResponse(content="", media_type="text/html; charset=utf-8")
    resp.headers["Vary"] = "Accept-Language"
    resp.headers["Content-Language"] = lang

    if cookie_action in SUPPORTED_LANGS:
        resp.set_cookie(
            LANG_COOKIE,
            cookie_action,
            max_age=31536000,
            httponly=False,
            samesite="lax",
        )
    elif cookie_action == "system":
        resp.delete_cookie(LANG_COOKIE)

    return resp


@app.get("/")
def root_index(request: Request):
    lang, cookie_action = _resolve_lang(request)
    html = _render_index_html(lang)

    resp = HTMLResponse(content=html, media_type="text/html; charset=utf-8")
    resp.headers["Vary"] = "Accept-Language"
    resp.headers["Content-Language"] = lang

    if cookie_action in SUPPORTED_LANGS:
        resp.set_cookie(
            LANG_COOKIE,
            cookie_action,
            max_age=31536000,
            httponly=False,
            samesite="lax",
        )
    elif cookie_action == "system":
        resp.delete_cookie(LANG_COOKIE)

    return resp


@app.get("/favicon.ico")
def favicon_ico():
    return FileResponse(STATIC_DIR / "favicon.ico")


@app.get("/favicon-32x32.png")
def favicon_32():
    return FileResponse(STATIC_DIR / "favicon-32x32.png")


@app.get("/favicon-16x16.png")
def favicon_16():
    return FileResponse(STATIC_DIR / "favicon-16x16.png")


@app.get("/apple-touch-icon.png")
def apple_touch_icon():
    return FileResponse(STATIC_DIR / "apple-touch-icon.png")
