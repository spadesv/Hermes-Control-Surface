---
name: Bug report
about: Report an installation, API, UI, config, or integration issue
title: "[Bug]: "
labels: bug
assignees: ""
---

## What happened?

Describe the issue clearly.

## Environment

- OS:
- Install method: release package / git clone / scripts/install.sh / manual
- Hermes Control Surface version:
- Browser and device, if UI-related:

## Commands

Please run these on the server and paste the output.

```bash
systemctl status hermes-control-surface.service --no-pager --full | sed -n '1,80p'
journalctl -u hermes-control-surface.service -n 100 --no-pager
curl -fsS http://127.0.0.1:9091/build-meta.json
curl -fsS http://127.0.0.1:9091/api/stats
bash scripts/doctor.sh
```

## Config

Paste only the relevant, redacted part of `config/config.yaml`.

Do not post tokens, passwords, public IP addresses, private hostnames, MAC addresses, or secrets.

## Screenshot

Attach a screenshot if this is a UI issue.
