# Installation

Hermes Control Surface is designed for a minimal Debian or Ubuntu server.

It runs as a small FastAPI service on port `9091`.

It does not require nginx.  
It does not require a `.env` file.  
The default install path is:

```text
/opt/hermes-control-surface
```

## Which install path should I use?

If you are new to the project, use the install script first:

```bash
sudo bash scripts/install.sh
```

If you want to understand or customize every step, use the manual install.

Both paths install the same service:

```text
hermes-control-surface.service
```

## Requirements

Required packages:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git curl ca-certificates
```

The dashboard uses Python dependencies from:

```text
requirements.txt
```

Optional features such as UPS or audio status may need extra system packages. They are listed later in this document.

## Option A: install script

Run this from the project source directory:

```bash
sudo bash scripts/install.sh
```

The script will:

```text
install basic Debian / Ubuntu packages
copy the project to /opt/hermes-control-surface
create a Python virtual environment
install Python dependencies
create config/config.yaml if missing
write the systemd service
start the dashboard on port 9091
```

It will not overwrite an existing:

```text
config/config.yaml
```

After it finishes, open:

```text
http://your-server-ip:9091/
```

## Option B: manual install

Use this path if you want to see each step.

### 1. Put the project under /opt

If you downloaded a release package:

```bash
sudo mkdir -p /opt
sudo tar -C /opt -xzf hermes-control-surface-v0.1.3.tar.gz
cd /opt/hermes-control-surface
```

If you cloned the repository:

```bash
sudo mkdir -p /opt
sudo cp -a hermes-control-surface /opt/hermes-control-surface
cd /opt/hermes-control-surface
```

If you are already inside `/opt/hermes-control-surface`, just continue.

### 2. Create a virtual environment

```bash
sudo python3 -m venv .venv
sudo .venv/bin/python -m pip install --upgrade pip
sudo .venv/bin/python -m pip install -r requirements.txt
```

### 3. Create local config

```bash
sudo cp config/config.example.yaml config/config.yaml
```

Then edit it:

```bash
sudo nano config/config.yaml
```

Your real `config/config.yaml` belongs only to your local machine.  
Do not publish it.

### 4. Create the systemd service

```bash
sudo tee /etc/systemd/system/hermes-control-surface.service >/dev/null <<'SERVICE_EOF'
[Unit]
Description=Hermes Control Surface
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/hermes-control-surface
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/hermes-control-surface/.venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 9091
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE_EOF
```

### 5. Start it

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-control-surface.service
```

### 6. Check it

```bash
curl -fsS http://127.0.0.1:9091/ >/dev/null
curl -fsS http://127.0.0.1:9091/api/stats >/dev/null
```

For a fuller read-only diagnostic report:

```bash
bash scripts/doctor.sh
```

Open:

```text
http://your-server-ip:9091/
```

## Optional features

Some cards depend on what exists on your machine.

You only need these packages if you want those features.

### UPS

For NUT / UPS status:

```bash
sudo apt install -y nut-client
```

Your NUT server still needs to be configured separately.

### Audio

For local audio status or control, your system may use packages such as:

```bash
sudo apt install -y bluez pipewire wireplumber mpv socat
```

Only install what your own setup needs.

## Config reload

`config.yaml` is hot-reloaded.

After editing it, the next API request will use the new config.

If YAML is invalid, the dashboard keeps the last known good config.

Code, HTML, and dependency changes still require a service restart:

```bash
sudo systemctl restart hermes-control-surface.service
```

## Logs and status

Check service status:

```bash
systemctl status hermes-control-surface.service --no-pager --full
```

Follow logs:

```bash
journalctl -u hermes-control-surface.service -f
```

Check the API:

```bash
curl -fsS http://127.0.0.1:9091/api/stats
```

## Firewall note

The dashboard listens on port `9091`.

If you can open it locally but not from another device, check your firewall or router rules.

## Uninstall

This removes the service and the installed application directory:

```bash
sudo systemctl disable --now hermes-control-surface.service
sudo rm -f /etc/systemd/system/hermes-control-surface.service
sudo systemctl daemon-reload
sudo rm -rf /opt/hermes-control-surface
```

If you want to keep your local config, back up this file first:

```text
/opt/hermes-control-surface/config/config.yaml
```
