#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${HCS_APP_DIR:-/opt/hermes-control-surface}"
SERVICE_NAME="${HCS_SERVICE_NAME:-hermes-control-surface.service}"
HOST="${HCS_HOST:-0.0.0.0}"
PORT="${HCS_PORT:-9091}"

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: please run this installer as root." >&2
  exit 1
fi

if ! command -v systemctl >/dev/null 2>&1; then
  echo "ERROR: systemd is required." >&2
  exit 1
fi

if [ ! -r /etc/os-release ]; then
  echo "ERROR: cannot read /etc/os-release." >&2
  exit 1
fi

. /etc/os-release

case "${ID:-}:${ID_LIKE:-}" in
  *debian*|*ubuntu*)
    ;;
  *)
    echo "WARNING: this installer is intended for Debian / Ubuntu style systems." >&2
    ;;
esac

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ ! -f "$SRC_DIR/server.py" ] || [ ! -d "$SRC_DIR/app" ] || [ ! -d "$SRC_DIR/static" ]; then
  echo "ERROR: install.sh must be run from a complete Hermes Control Surface source tree." >&2
  exit 1
fi

echo "===== install system packages ====="
apt-get update
apt-get install -y python3 python3-venv python3-pip curl ca-certificates

echo "===== prepare application directory: $APP_DIR ====="
mkdir -p "$APP_DIR"

SRC_REAL="$(realpath "$SRC_DIR")"
APP_REAL="$(realpath "$APP_DIR")"

if [ "$SRC_REAL" != "$APP_REAL" ]; then
  echo "Copying source files to $APP_DIR"
  tar -C "$SRC_DIR" \
    --exclude='./config/config.yaml' \
    --exclude='./.git' \
    --exclude='./.venv' \
    --exclude='./venv' \
    --exclude='./logs' \
    --exclude='./runtime' \
    --exclude='./data' \
    --exclude='./__pycache__' \
    --exclude='./*/__pycache__' \
    --exclude='./*/*/__pycache__' \
    --exclude='./*/*/*/__pycache__' \
    --exclude='./*.pyc' \
    --exclude='./*/*.pyc' \
    --exclude='./*/*/*.pyc' \
    --exclude='./*/*/*/*.pyc' \
    --exclude='./*.bak' \
    --exclude='./*.bak.*' \
    --exclude='./*/*.bak' \
    --exclude='./*/*/*.bak' \
    --exclude='./*/*.bak.*' \
    --exclude='./*/*/*.bak.*' \
    -cf - . | tar -C "$APP_DIR" -xf -
else
  echo "Source directory is already $APP_DIR; skipping copy."
fi

echo "===== ensure local config exists ====="
if [ ! -f "$APP_DIR/config/config.yaml" ]; then
  if [ -f "$APP_DIR/config/config.example.yaml" ]; then
    cp -a "$APP_DIR/config/config.example.yaml" "$APP_DIR/config/config.yaml"
    echo "Created $APP_DIR/config/config.yaml from example."
  else
    echo "ERROR: missing config/config.example.yaml." >&2
    exit 1
  fi
else
  echo "Keeping existing $APP_DIR/config/config.yaml"
fi

echo "===== create Python virtual environment ====="
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/python" -m pip install --upgrade pip
"$APP_DIR/.venv/bin/python" -m pip install -r "$APP_DIR/requirements.txt"

echo "===== write systemd service ====="
cat > "/etc/systemd/system/$SERVICE_NAME" <<SERVICE_EOF
[Unit]
Description=Hermes Control Surface
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$APP_DIR/.venv/bin/python -m uvicorn server:app --host $HOST --port $PORT
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE_EOF

echo "===== start service ====="
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"

sleep 2

echo "===== health check ====="
curl -fsS "http://127.0.0.1:$PORT/" >/dev/null
curl -fsS "http://127.0.0.1:$PORT/api/stats" >/dev/null

echo
echo "Hermes Control Surface is running."
echo "Local URL:  http://127.0.0.1:$PORT/"
echo "LAN URL:    http://<your-server-ip>:$PORT/"
echo
echo "Config:     $APP_DIR/config/config.yaml"
echo "Service:    $SERVICE_NAME"
