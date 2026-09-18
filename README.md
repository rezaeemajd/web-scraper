# Cofinets Data Intelligence (CDI)

Production-oriented web data acquisition and intelligence platform for Cofinets.

## Current branch

This implementation branch is intentionally isolated from main:

cdi-v1-foundation

The existing main branch is not modified.

## Goals

- Generic entity/data model with Healthcare-first taxonomy
- Source and scraper management
- Safe HTTP crawling with domain scope, robots policy, rate limits and retries
- Parsing, extraction, normalization, validation and deduplication
- Provenance, quality, review and auditability
- PostgreSQL + Redis + Celery
- Persian RTL dashboard
- CSV, XLSX, JSON, JSONL, DOCX and PDF export architecture
- Docker production deployment
- Non-destructive deployment alongside the existing Cofinets services

## Safety

Only public and permitted web data is in scope. The platform does not implement CAPTCHA bypass, authentication bypass, paywall bypass, private-data extraction or security-control evasion.

## Deployment target

The intended hostname is data.cofinets.com, but it must be selected only after inspecting the current DNS and Nginx configuration on the production server.

The existing Cofinets application, Docker project, volumes, networks, PostgreSQL data and Nginx sites must remain untouched.

## Server constraints

The known production server is Debian 13 with 2 CPU cores and 2 GB RAM. CDI therefore uses conservative worker counts, low browser concurrency, explicit memory limits and isolated Docker resources.

## Documentation

The full implementation will include architecture, deployment, scraper, parser, data model, security, exports, operations and troubleshooting documentation.

## Production rule

No claim of successful deployment, test execution, ZIP creation or checksum is made until the corresponding operation has actually been executed and verified.
