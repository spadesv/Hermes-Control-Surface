# Usage

Hermes Control Surface is intentionally small.

It was built around a real local machine first, then cleaned up for sharing.  
The configuration is practical rather than abstract: define what you actually run, then decide what should appear on the page.

## 1. Mental model

The dashboard has three layers:

```text
config/config.yaml
  -> backend status APIs
  -> frontend visibility and layout
```

The backend collects status.  
The frontend decides how to display it.  
Capabilities decide what should be visible.

## 2. Start or restart

For daily use, run it with systemd:

```bash
sudo systemctl restart hermes-control-surface.service
```

For a quick local test from the project directory:

```bash
python3 -m uvicorn server:app --host 0.0.0.0 --port 9091
```

Open:

```text
http://your-host:9091/
```

## 3. Local config

Create your local config:

```bash
cp config/config.example.yaml config/config.yaml
```

Edit it:

```bash
nano config/config.yaml
```

Do not commit your real `config/config.yaml`.

This project does not require a `.env` file.

## 4. Hot reload

`config.yaml` is hot-reloaded.

After you save the file, the next API request will use the new config.

If the YAML is broken, the dashboard keeps using the last known good config.

Code, HTML, and dependency changes still need a service restart:

```bash
sudo systemctl restart hermes-control-surface.service
```

## 5. Language

Language priority:

```text
?lang parameter
> saved language cookie
> browser Accept-Language
> default language
```

Useful URLs:

```text
/?lang=en
/?lang=zh-CN
/?lang=system
```

`system` clears the saved language choice and follows the browser again.

## 6. Responsive layout

The dashboard is designed for both desktop and mobile use.

Desktop:

```text
wide layout
larger hero area
more information visible at once
```

Mobile:

```text
compact header
stacked cards
single-column sections on small screens
bottom-sheet style settings drawer
```

The mobile layout is not a separate app.  
It is the same dashboard, adjusted for smaller screens.

## 7. Capabilities

Capabilities decide what appears on the page.

```yaml
dashboard:
  sections:
    network: auto
    audio: hide

  cards:
    ups: auto

  platforms:
    telegram: show
    discord: hide

  services:
    docker: show
    crowdsec: hide
```

Values:

```text
auto  default behavior
show  force visible
hide  force hidden
```

This only controls the display.  
It does not change your system services.

## 8. Services

The dashboard does not scan every systemd service.

You define the services you care about:

```yaml
services:
  hermes: hermes-gateway
  docker: docker
  crowdsec: crowdsec
```

Then control visibility:

```yaml
dashboard:
  services:
    hermes: show
    docker: show
    crowdsec: hide
```

This makes the service list predictable.

## 9. Optional integrations

Some parts depend on your own machine.

Examples:

```text
UPS       requires a working NUT setup
Audio     depends on your local PipeWire / Bluetooth / mpv setup
Network   depends on the commands or interfaces you configure
Services  depend on the systemd units you list
```

If a feature is not relevant to your setup, hide it with capabilities.

## 10. Quick checks

Basic health:

```bash
curl -fsS http://127.0.0.1:9091/ >/dev/null
curl -fsS http://127.0.0.1:9091/api/stats >/dev/null
```

Language:

```bash
curl -sD - -o /dev/null \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' \
  http://127.0.0.1:9091/ | grep -i content-language
```

Service status:

```bash
systemctl status hermes-control-surface.service --no-pager --full
```

Logs:

```bash
journalctl -u hermes-control-surface.service -f
```

## 11. Common questions

### The page does not open

Check the service:

```bash
systemctl status hermes-control-surface.service --no-pager --full
```

Check the port:

```bash
ss -lntp | grep ':9091'
```

Check local access:

```bash
curl -fsS http://127.0.0.1:9091/ >/dev/null
```

### Config changes do not appear

Save `config/config.yaml`, then refresh the page.

If the YAML is invalid, the dashboard keeps the last known good config. Check logs:

```bash
journalctl -u hermes-control-surface.service -n 80 --no-pager
```

### A card or row is missing

Check the corresponding capability value:

```yaml
auto
show
hide
```

If it is set to `hide`, the frontend will hide it.

### A service row shows offline

Check the real systemd unit name:

```bash
systemctl status your-service-name
```

Then make sure the same name is listed in `config.yaml`.

## 12. If you fork or republish this project

If you are only using the dashboard locally, you can skip this section.

If you plan to fork, package, or publish your own modified version, make sure you are not including private or generated files.

Do not publish:

```text
config/config.yaml
*.bak.*
__pycache__
*.pyc
runtime data
cache files
local screenshots with private information
```

Safe public files usually include:

```text
config/config.example.yaml
README.md
README.zh-CN.md
docs/
server.py
app/
static/
scripts/
requirements.txt
```

Your real `config/config.yaml` belongs only to your local machine.  
Public repositories should use `config/config.example.yaml`.
