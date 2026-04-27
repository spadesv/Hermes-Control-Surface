# Changelog

## v0.1.2 - Diagnostics and settings polish

This release focuses on support readiness, diagnostics, and a small settings UI polish pass.

It includes:

- Added `scripts/doctor.sh` for read-only environment diagnostics
- Added safe `collector_errors` in `/api/stats` for support troubleshooting
- Kept Hermes Agent metadata separate from Hermes Control Surface build metadata
- Added a refined settings drawer build footer driven by `/build-meta.json`
- Added configuration reference documentation and issue templates
- Updated release metadata and package references for `v0.1.2`

## v0.1.1 - Dynamic rows and release hardening

This release focuses on making the public package safer and more extensible.

It includes:

- Dynamic service rows driven by configured `services:` keys
- Dynamic platform rows driven by Hermes gateway state
- Safer `/api/stats` collector isolation so one failing module does not break the whole API
- Cleaner public defaults and corrected Hermes gateway service documentation
- More robust config-section access shared through `config_loader`
- Broader disk, temperature, UPS, and Bluetooth status compatibility
- Documentation and package references updated for `v0.1.1`

## v0.1.0 - Initial public release

This is the first public release of Hermes Control Surface.

It includes:

- English and Simplified Chinese dashboard pages
- Browser-language based routing with manual language selection
- Hot-reloaded YAML configuration
- Capability-based display controls for sections, cards, platforms, and services
- Local system, storage, network, UPS, audio, and selected service status blocks
- Desktop and mobile responsive layout
- Debian / Ubuntu installation documents
- Optional `scripts/install.sh` installer

This release is intentionally small. It started as a personal local dashboard and is now being shared as a clean starting point for people with similar environments.
