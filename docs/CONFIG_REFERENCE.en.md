# Hermes Control Surface Configuration Reference

This reference explains the public YAML model used by Hermes Control Surface.

Copy the example file before editing:

```bash
cp config/config.example.yaml config/config.yaml
```

Never commit your private `config/config.yaml`.

## Core fields

| Path | Purpose | Notes |
|---|---|---|
| `site.page_title` | Browser title | Display-only |
| `site.port` | Example service port | Default release setup uses `9091` |
| `frontend.badge_*` | Top badges | Empty value means auto-detect when possible |
| `frontend.brand_*` | Header brand text | Rendered by `server.py` |
| `build.*` | HCS build metadata | Used by `/build-meta.json` and Settings footer |
| `agent.*` | Hermes Agent paths | Used to read Agent version, model, gateway state, cron jobs |
| `network.*` | WAN/proxy/gateway display | Optional; disable if not needed |
| `services.*` | Systemd unit allow-list | Drives dynamic service rows |
| `ups.*` | NUT UPS integration | HCS reads NUT; it does not configure NUT |
| `bluetooth.*` | Bluetooth speaker status | Optional |
| `mpv.*` | MPV IPC status | Optional |
| `cron_display_names` | Friendly cron names | Display-only mapping |
| `dashboard.*` | UI visibility policies | `auto`, `show`, or `hide` |

## Services vs dashboard.services

`services:` defines what to check.

```yaml
services:
  docker: docker
  nginx: nginx
```

`dashboard.services:` controls whether a row is displayed.

```yaml
dashboard:
  services:
    docker: show
    nginx: auto
```

Hermes Control Surface does not scan every systemd service. Users must explicitly list services they want to monitor.

## Platforms

Platform rows are generated dynamically from Hermes gateway state and `dashboard.platforms`.

```yaml
dashboard:
  platforms:
    telegram: auto
    discord: auto
    homeassistant: auto
```

If a future gateway state includes `slack` or `matrix`, HCS can display it without hardcoded frontend rows.

## Display policies

| Value | Meaning |
|---|---|
| `auto` | Show only when related config/data exists |
| `show` | Force show |
| `hide` | Force hide |

## Build metadata

`build:` is the Hermes Control Surface version, not the Hermes Agent version.

```yaml
build:
  version: 0.1.3
  build_date: "2026-05-16"
  commit: v0.1.3
  channel: stable
```

Agent metadata is shown separately in `/api/stats.agent`.

## Hot reload

Valid YAML changes usually apply on the next API request. Python, HTML, and dependency changes require a service restart.
