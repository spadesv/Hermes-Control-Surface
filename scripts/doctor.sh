#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd -P)"
DEFAULT_APP_DIR="$(cd -- "$SCRIPT_DIR/.." >/dev/null 2>&1 && pwd -P)"

APP_DIR="${APP_DIR:-$DEFAULT_APP_DIR}"
SERVICE="${SERVICE:-hermes-control-surface.service}"
BASE_URL="${BASE_URL:-http://127.0.0.1:9091}"

ok() { echo "OK: $*"; }
warn() { echo "WARN: $*"; }
fail() { echo "FAIL: $*"; }

http_code() {
  local path="$1"
  curl -sS -o /dev/null -w '%{http_code}' "${BASE_URL}${path}" 2>/dev/null || true
}

echo
echo "===== Hermes Control Surface doctor ====="
echo "App dir: $APP_DIR"
echo "Service: $SERVICE"
echo "Base URL: $BASE_URL"
date -Is || true

echo
echo "===== System ====="
if [ -f /etc/os-release ]; then
  sed -n '1,12p' /etc/os-release
else
  warn "/etc/os-release not found"
fi
python3 --version 2>/dev/null || warn "python3 not found"
systemctl --version 2>/dev/null | head -1 || warn "systemctl not found"
curl --version 2>/dev/null | head -1 || warn "curl not found"

echo
echo "===== Project files ====="
cd "$APP_DIR" 2>/dev/null || {
  fail "cannot cd to $APP_DIR"
  exit 1
}

for f in \
  server.py \
  requirements.txt \
  config/config.example.yaml \
  static/index.en.html \
  static/index.zh-CN.html
do
  if [ -f "$f" ]; then
    ok "$f exists"
  else
    fail "$f missing"
  fi
done

if [ -f config/config.yaml ]; then
  ok "private config/config.yaml exists"
else
  warn "private config/config.yaml does not exist; example config will be used"
fi

echo
echo "===== YAML parse ====="
python3 - <<'PY'
from pathlib import Path
import yaml

for name in ["config/config.example.yaml", "config/config.yaml"]:
    p = Path(name)
    if not p.exists():
        print(f"WARN: {name} not found")
        continue
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            print(f"OK: {name} parses as YAML mapping")
        else:
            print(f"FAIL: {name} is not a YAML mapping")
    except Exception as exc:
        print(f"FAIL: {name} YAML parse failed: {exc}")
PY

echo
echo "===== Python syntax ====="
PYCACHE="$(mktemp -d)"
if PYTHONPYCACHEPREFIX="$PYCACHE" python3 -m py_compile server.py app/*.py app/api/*.py 2>/tmp/hcs-doctor-pycompile.err; then
  ok "Python syntax passed"
else
  fail "Python syntax failed"
  sed -n '1,120p' /tmp/hcs-doctor-pycompile.err
fi
rm -rf "$PYCACHE" /tmp/hcs-doctor-pycompile.err

echo
echo "===== Service ====="
if systemctl status "$SERVICE" --no-pager --full >/tmp/hcs-doctor-service.txt 2>&1; then
  ok "$SERVICE is active or status returned successfully"
else
  warn "systemctl status returned non-zero"
fi
sed -n '1,35p' /tmp/hcs-doctor-service.txt
rm -f /tmp/hcs-doctor-service.txt

echo
echo "===== Port ====="
if ss -lntp 2>/dev/null | grep -q ':9091'; then
  ok "port 9091 is listening"
  ss -lntp 2>/dev/null | grep ':9091' || true
else
  warn "port 9091 is not listening"
fi

echo
echo "===== HTTP checks ====="
for path in "/" "/?lang=en" "/?lang=zh-CN" "/api/stats" "/api/public-config" "/api/cron-jobs" "/build-meta.json"; do
  code="$(http_code "$path")"
  if [ "$code" = "200" ]; then
    ok "GET $path -> 200"
  else
    warn "GET $path -> ${code:-no response}"
  fi
done

echo
echo "--- build-meta.json ---"
if curl -fsS "$BASE_URL/build-meta.json" -o /tmp/hcs-doctor-build-meta.json 2>/tmp/hcs-doctor-build-meta.err; then
  python3 -m json.tool /tmp/hcs-doctor-build-meta.json 2>/dev/null || cat /tmp/hcs-doctor-build-meta.json
else
  warn "cannot fetch build-meta.json"
  sed -n '1,80p' /tmp/hcs-doctor-build-meta.err
fi
rm -f /tmp/hcs-doctor-build-meta.json /tmp/hcs-doctor-build-meta.err

echo
echo "--- api/stats summary ---"
if curl -fsS "$BASE_URL/api/stats" -o /tmp/hcs-doctor-stats.json 2>/tmp/hcs-doctor-stats.err; then
  python3 - <<'PY'
import json
from pathlib import Path

p = Path("/tmp/hcs-doctor-stats.json")
try:
    data = json.loads(p.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"WARN: cannot parse stats JSON: {exc}")
    raw = p.read_text(encoding="utf-8", errors="replace")
    print(raw[:500])
    raise SystemExit(0)

agent = data.get("agent") or {}
services_list = data.get("services_list") or []
disks = data.get("disks") or []

summary = {
    "agent": agent,
    "collector_errors": data.get("collector_errors"),
    "services_keys": sorted((data.get("services") or {}).keys()),
    "services_list_keys": [x.get("key") for x in services_list if isinstance(x, dict)],
    "platforms": (data.get("capabilities") or {}).get("platforms"),
    "disks": [
        {
            "mount": x.get("mount"),
            "device": x.get("device"),
            "model": x.get("model"),
            "total_gb": x.get("total_gb"),
            "used_gb": x.get("used_gb"),
            "percent": x.get("percent"),
        }
        for x in disks[:6]
        if isinstance(x, dict)
    ],
}
print(json.dumps(summary, ensure_ascii=False, indent=2))

print()
print("--- disk display summary ---")
if not disks:
    print("WARN: no disks returned by /api/stats")
else:
    for disk in disks[:6]:
        if not isinstance(disk, dict):
            continue
        print(
            "- {mount} {device} {model} {used}/{total}GB {percent}%".format(
                mount=disk.get("mount") or "—",
                device=disk.get("device") or "—",
                model=disk.get("model") or "—",
                used=disk.get("used_gb", "—"),
                total=disk.get("total_gb", "—"),
                percent=disk.get("percent", "—"),
            )
        )

print()
print("--- metadata separation check ---")
print("Hermes Agent version:", agent.get("version") or "—")
print("Hermes Agent commit:", agent.get("commit") or "—")
print("HCS build metadata: see /build-meta.json above")
PY
else
  warn "cannot fetch /api/stats"
  sed -n '1,80p' /tmp/hcs-doctor-stats.err
fi
rm -f /tmp/hcs-doctor-stats.json /tmp/hcs-doctor-stats.err

echo
echo "===== Frontend dynamic-row and footer markers ====="
grep -RInE 'servicesList|renderServices|platformsList|renderPlatforms|settings-build-footer|settingsBuildVersion|settingsBuildDate' \
  static/index.en.html static/index.zh-CN.html 2>/dev/null | sed -n '1,180p' || warn "expected frontend markers not found"

echo
echo "===== Known-bad frontend markers ====="
bad="$(grep -RInE 'HCS_SETTINGS_BUILD_FOOTER|findSettingsPanel|setService\(|telegramStatus|discordStatus|haStatus|data-service=\"hermes\"|data-platform=\"telegram\"' \
  static/index.en.html static/index.zh-CN.html 2>/dev/null || true)"
if [ -n "$bad" ]; then
  echo "$bad"
  warn "known-bad or old hardcoded frontend markers found"
else
  ok "no known-bad frontend markers found"
fi

echo
echo "===== Local artifacts in app tree ====="
echo "Note: runtime Python caches are normal and are intentionally not listed here."
find . \
  -path './.venv' -prune -o \
  -path './.venv/*' -prune -o \
  \( -name '.pytest_cache' \
  -o -name '.mypy_cache' \
  -o -name '.ruff_cache' \
  -o -name '.coverage' \
  -o -name 'htmlcov' \
  -o -name '.DS_Store' \
  -o -name 'Thumbs.db' \
  -o -name '.audit-backup' \
  -o -name '*.tmp' \
  -o -name '*~' \
  \) -print 2>/dev/null | sed -n '1,120p' || true

echo
echo "===== Runtime config backups ====="
find config -maxdepth 1 -type f -name 'config.yaml.bak*' -print 2>/dev/null | sort | sed -n '1,60p' || true

echo
echo "===== Done ====="
echo "Doctor completed. Review WARN/FAIL lines above."
