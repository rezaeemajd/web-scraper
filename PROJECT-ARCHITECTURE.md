# 🏗️ PROJECT ARCHITECTURE — Cofinets Data Intelligence (CDI)

> مرجع ساختار پروژه، محیط‌ها، سرویس‌ها، قابلیت‌ها و قراردادهای اجرایی. این فایل باید همراه با project-prombt.md و PROJECT_STATUS.md قبل از هر مرحله مرور و پس از تغییر معماری به‌روزرسانی شود.

## 1. Product

**Name:** Cofinets Data Intelligence  
**Short name:** CDI  
**Primary domain target:** cofinets.com  
**Initial market:** Iran / Healthcare / Pharmaceutical  
**Primary entities:** Drug, Vaccine, Pharmacy, Doctor, Office, Clinic, Company/Manufacturer  
**Core principle:** generic entity/data engine + healthcare-specific plugins/configuration.

## 2. Core data flow

SOURCE → DISCOVERY → FETCH → PARSE → EXTRACT → NORMALIZE → VALIDATE → DEDUPLICATE → QUALITY → REVIEW → APPROVE → STORE → ANALYZE → EXPORT

### Important semantic separation

Product identity ≠ Pharmacy listing ≠ Availability observation ≠ Current stock ≠ Price observation ≠ Legal/import status

این تفکیک از اشتباه رایج تبدیل یک صفحه محصول به ادعای موجودی فعلی جلوگیری می‌کند.

## 3. Repository structure

web-scraper/
├── project-prombt.md             # قانون اساسی پروژه — قبل از هر کار
├── PROJECT_STATUS.md              # وضعیت زنده و نقطه ادامه
├── PROJECT-ARCHITECTURE.md        # همین سند — ساختار و قابلیت‌ها
├── README.md
├── backend/
│   ├── config/                    # Django settings / URLs / Celery
│   ├── core/                      # health / readiness / permissions
│   ├── sources/                   # source registry + safe fetching
│   ├── scraping/                  # scraper definition + engine + tasks
│   ├── datahub/                   # generic entity/data/identity/review
│   ├── exports/                   # CSV/XLSX/JSON/JSONL/TXT/DOCX/PDF
│   ├── requirements.txt
│   └── manage.py
├── frontend/
│   └── ...                        # Next.js / React / TypeScript / RTL
├── docs/
│   ├── project-status.md          # historical/branch continuation notes
│   └── market-benchmark-gardasil-iran.md
├── docker-compose.yml
└── .github/workflows/             # backend/frontend/docker/compose CI

## 4. Current backend capabilities

### Core
- Django
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- health/readiness endpoints
- authentication پایه
- staff-write permission boundary

### Source / Fetch
- source registry
- robots-aware fetch
- source-domain restriction
- safe redirect handling
- public-IP / SSRF checks
- rate limiting
- response-size limit
- raw response capture
- SHA256 body fingerprint
- reusable HTTP client path

### Extraction
- CSS selector fields
- label-table extraction
- regex fields
- evidence per extracted field
- bounded pagination
- parser versioning
- single-step execution
- compatibility with scraper adapters

### Data
- generic EntityType / EntityField
- dynamic payload
- normalized payload
- location reference
- raw capture provenance
- quality/confidence
- fingerprint
- validation errors
- observation history
- change history

### Identity / Dedup
- exact fingerprint constraints
- configured blocking fields
- bounded PostgreSQL JSONB candidate search
- symmetric sparse-record similarity
- candidate threshold 0.6500
- candidate review instead of automatic destructive merge
- merge/resolve workflow foundation

### API
- Entity Types
- Entity Fields
- Locations
- Raw Captures
- Extracted Records
- Dedup Candidates
- Review Tasks
- Audit Events
- Observations
- Changes
- filtering/search/ordering
- deterministic list ordering
- list serializers that avoid large JSON/raw payloads

### Export
- CSV
- XLSX
- JSON
- JSONL
- TXT
- DOCX
- PDF
- streaming QuerySet iteration for bounded memory use

## 5. Current Docker topology

Nginx / future staging proxy
        |
Frontend :3000
        |
Backend :8000
        |
  +-----+-----+
  |           |
PostgreSQL  Redis
  |
Worker / Beat

Current compose bindings are loopback-only:
- backend host: 127.0.0.1:8001 → container:8000
- frontend host: 127.0.0.1:3001 → container:3000
- PostgreSQL: internal Docker network
- Redis: internal Docker network

Resource intent for the 2GB class server:

| Service | Limit | Purpose |
|---|---:|---|
| PostgreSQL | host-managed / DB container | persistent data |
| Redis | 128 MB configured | cache + Celery |
| Backend | 384 MB | API / Django |
| Worker | 256 MB | scraping/export tasks |
| Beat | 128 MB | scheduler |
| Frontend | 256 MB | Next.js |

Worker:
- concurrency: 1
- prefetch multiplier: 1
- max tasks per child: 50
- queues: scraping, exports

## 6. Production server boundary

### Existing Cofinets production — VERIFIED FROM PROJECT CONTEXT

srv4237180295
Debian 13
2 vCPU
2 GB RAM
50 GB
45.149.78.10

Existing services:
- cofinets_web
- cofinets_db
- Nginx
- Cloudflare/TLS
- cofinets.com
- cofinets.ir

CDI must not modify these services during staging.

Rules:
1. Backup before production changes.
2. Never use docker compose down on shared production stack.
3. Never use docker system prune.
4. No broad UFW changes.
5. No unrelated Xray changes.
6. New Nginx config goes into a separate file.
7. Run nginx -t before reload.
8. If health check fails, rollback the new CDI layer only.
9. Database rollback follows migration/backup strategy; never improvise destructive DB operations.

## 7. CDI deployment boundary

Production Cofinets
        X
        |
        | isolated
        ↓
CDI staging
  ├── cdi-postgres
  ├── cdi-redis
  ├── cdi-backend
  ├── cdi-worker
  ├── cdi-beat
  └── cdi-frontend

No live server execution is claimed by this document unless a later status entry explicitly records command output and date.

## 8. Real-market benchmark

Primary acceptance dataset: Gardasil 9 — Iran.

Verified public source pages currently used:
- Pillix med-mivz
- Pillix med-bhl4

Benchmark:
real URL → real HTTP response → real extraction → real normalization → real DB transaction → real API retrieval

No fake records for acceptance.

## 9. Pharmacy phase

Location
  └── Pharmacy

MarketObservation
  ├── pharmacy
  ├── product/record
  ├── observed_at
  ├── availability
  ├── price nullable
  ├── source
  ├── source_url
  ├── raw_capture
  └── evidence

Do not encode current stock as a permanent Product property.

### Current PR implementation

The active P1 branch now contains Pharmacy and MarketObservation model/API foundations plus migration 0010. They remain isolated in the PR until CI and real-data acceptance are completed.

## 10. Frontend target

Next.js + React + TypeScript + Tailwind.

Requirements:
- RTL Persian
- responsive
- mobile-first
- desktop usable
- dark/light ready
- real API data
- search/filter/sort/pagination
- source/provenance visible
- observation timestamp visible
- review/quality state visible where appropriate

The UI must be built against real CDI API data, not mock market records.

## 11. Security boundary

Allowed:
- public web data
- robots-compliant crawling
- source-specific rate limits
- public APIs
- public HTML/JSON/XML/PDF
- explicit public business contact information

Forbidden:
- CAPTCHA bypass
- login bypass
- paywall bypass
- security bypass
- private data extraction
- account takeover
- attack traffic
- stealth/evasion intended to defeat access controls

## 12. Operational workflow

1. Read project-prombt.md
2. Read PROJECT_STATUS.md
3. Read PROJECT-ARCHITECTURE.md
4. Inspect current branch/PR/CI
5. Inspect relevant code
6. Search official documentation when behavior matters
7. Search real market source when data model matters
8. Implement the smallest production-useful change
9. Run only relevant tests
10. Record actual result
11. Update PROJECT_STATUS.md
12. Update PROJECT-ARCHITECTURE.md if topology/capability changed
13. Continue to next useful phase

## 13. CI / QA policy

Required gates:
- migrations
- backend tests
- Docker build
- compose integration
- frontend build
- security-sensitive fetcher tests
- real Gardasil acceptance on isolated environment

Do not repeatedly rerun an unchanged failing test. First inspect the failure and fix its root cause.

## 14. Backup / restore

Before production deployment:
- full backup
- database backup
- configuration backup
- Nginx configuration backup
- deployment manifest/version recorded
- rollback commands documented

Retention and raw capture cleanup must remain configurable.

## 15. Future capabilities — intentionally deferred

Only introduce after real need:
- Playwright for JS-only sources
- PDF/OCR
- advanced maps
- WebSocket live monitoring
- OpenSearch
- advanced analytics
- multi-tenancy
- commercial API
- ML-based entity resolution

Current priority is reliable collection and useful data, not architectural complexity.

## 16. Definition of Done for CDI v1

- [ ] authentication
- [ ] RBAC
- [ ] source management
- [ ] scraper management
- [ ] parser/extraction
- [ ] normalization
- [ ] validation
- [ ] dedup/review
- [ ] observations/change history
- [ ] real Gardasil acceptance
- [ ] Pharmacy + geography
- [ ] real bounded pharmacy crawl
- [ ] Data Explorer
- [ ] exports
- [ ] scheduler
- [ ] logs/error center
- [ ] backup/restore
- [ ] isolated staging
- [ ] Nginx/HTTPS staging
- [ ] production deployment with rollback

## 17. Current next execution block

1. Verify latest CI result once.
2. Do not rerun CI without a new root cause.
3. Run real two-page Gardasil benchmark on isolated stack.
4. Verify dry-run rollback.
5. Persist and repeat for idempotency.
6. Implement Pharmacy + MarketObservation.
7. Run bounded Tehran/Gardasil crawl.
8. Expose real Explorer API.
9. Build RTL Explorer.
10. Stage and verify resource/backup/rollback.


## 2026-09-20 — 12:38 +03:30 — Architecture Continuation Update

### وضعیت پیاده‌سازی فعلی
- Discovery و Fetch در مسیر واحد قرار گرفته‌اند: Source → bounded discovery → RawCapture → source Adapter → extraction summary.
- Adapter Registry نقطه انتخاب parser است و Generic JSON-LD فقط با شواهد schema.org/Product رکورد Product تولید می‌کند.
- Adapter اختصاصی برای ساختارهای متفاوت Sourceها ضروری است؛ Generic parser جایگزین semantic/source-specific parsing نیست.
- گام بعدی: خروجی extraction وارد datahub.pipeline.process_records() شود تا provenance، normalization، identity، fingerprint و observation پایدار ثبت شوند.

### قرارداد چندمنبعی
Source/Domain → Discovery → Adapter → ExtractedRecord → Normalization/Identity → Observation

هر Source مستقل فرض می‌شود و تفاوت HTML، schema، semantics، pagination و evidence در Adapter همان Source مدیریت می‌شود.

### Benchmark واقعی
- Gardasil 9 در Pillix benchmark واقعی اطلاعات محصول/دارویی است.
- پذیرش CDI با یک URL انجام نمی‌شود؛ چند domain مستقل و چند نوع Source لازم است.
- regulatory/product، retail listing، pharmacy availability و price observation در لایه‌های معنایی جدا هستند.

### Production boundary
این مرحله فقط روی branch/PR ایزوله است؛ Production Cofinets دست‌نخورده است و اجرای live staging بدون command output ثبت‌شده ادعا نمی‌شود.

### گام بعدی معماری
Adapter output → process_records() → ExtractedRecord → RecordObservation/RecordChange → API → real RTL Explorer؛ سپس Pharmacy/MarketObservation و crawl محدود تهران پس از اثبات داده واقعی.


## 2026-09-20 — 12:58 +03:30 — Pipeline integration architecture update

### جریان اجرایی فعلی
`Source → bounded discovery → safe RawCapture → source adapter → adapter_record_to_item → process_records → ExtractedRecord → RecordObservation/RecordChange`

### Provenance contract
هر رکورد استخراج‌شده در این مسیر، تا حد امکان این زنجیره را حفظ می‌کند:
- source domain
- source URL
- detail URL در صورت وجود
- RawCapture ID
- evidence type
- payload و normalized payload
- observation fingerprint

captureهای موفق تنها ورودی persist pipeline هستند؛ خطا و block فقط در گزارش run باقی می‌مانند.

### Dry-run contract
command بدون `--persist` کل عملیات DB را داخل transaction اجرا و در پایان rollback می‌کند؛ بنابراین discovery، Source، RawCapture، EntityType/Field و records ایجادشده در dry-run commit نمی‌شوند. این با مدل transaction اتمیک Django هم‌راستاست. 

### مرز semantic
`Product` در این مرحله یک entity عمومی برای خروجی Adapter است؛ قیمت و availability صرفاً داده مشاهده‌شده هستند و نباید به‌عنوان حقیقت دائمی محصول تفسیر شوند. برای sourceهای پزشکی/رگولاتوری و marketplace در benchmark بعدی adapterهای جداگانه و semantics مستقل لازم است.

### تغییر نسبت به معماری قبلی
قبلاً discovery فقط extraction summary تولید می‌کرد؛ اکنون خروجی Adapter وارد Core data pipeline می‌شود. این تغییر capability معماری است و از این تاریخ در benchmark واقعی استفاده خواهد شد.
