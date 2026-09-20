# 📌 PROJECT STATUS — Cofinets Data Intelligence (CDI)

> سند زنده وضعیت پروژه. قبل از هر مرحله باید این فایل و project-prombt.md و PROJECT-ARCHITECTURE.md مرور شوند. این سند فقط وضعیت واقعیِ مشاهده‌شده را ثبت می‌کند؛ اجرای انجام‌نشده به‌عنوان Done نوشته نمی‌شود.

## 🎯 هدف کل پروژه

ساخت یک Web Data Acquisition و Market Intelligence Platform واقعی، سبک، امن و قابل استقرار برای جمع‌آوری داده‌های عمومی وب؛ تمرکز نسخه اول روی دارو، واکسن، داروخانه، پزشک، مطب و کلینیک در ایران و حفظ Generic بودن Core برای حوزه‌های آینده.

چرخه ستون فقرات:

SOURCE → DISCOVERY → FETCH → PARSE → EXTRACT → NORMALIZE → VALIDATE → DEDUPLICATE → QUALITY → REVIEW → APPROVE → STORE → ANALYZE → EXPORT

## 📈 درصد پیشرفت کل

- **برآورد فعلی:** 63%
- **باقی‌مانده:** 37%
- درصدها شاخص مهندسی برای مدیریت فازها هستند، نه ادعای پوشش کامل Production.

## 🌐 وضعیت GitHub

- Repository: rezaeemajd/web-scraper
- Main: مستندات مرجع پروژه در ریشه repository قرار دارند.
- Foundation: cdi-v1-foundation
- Foundation commit: c072da00dfce2d3c5c27b11c499a73c45343c95b
- P1 branch: cdi-v1-p1-core-data-engine
- PR #1: Open / Draft / Not Merged
- PR #1 base: Foundation
- آخرین head شناخته‌شده PR: a80761ecc87830ba1ab784b85bc148e1d5c100e5
- PR mergeable: در آخرین بررسی GitHub، true
- CI: روی head قبلی 6540ce7 یک شکست مشخص در `makemigrations --check` ثبت شد؛ علت اختلاف نام خودکار indexهای Pharmacy/MarketObservation با migration 0010 بود. این اختلاف در head جدید f3affe3 با تثبیت نام indexها اصلاح شده و CI جدید هنوز نتیجه نهایی ندارد.
- تغییرات Foundation و Production عمداً انجام نشده‌اند.

## 🖥️ وضعیت سرور

### Production موجود Cofinets
- Host: srv4237180295
- Debian 13
- 2 vCPU / 2 GB RAM / 50 GB
- Existing services: cofinets_web, cofinets_db
- Nginx و دامنه‌های موجود Cofinets فعال و خارج از scope تغییرات CDI
- **CDI روی Production Deploy نشده است.**
- هیچ سرویس موجودی برای CDI متوقف یا rebuild نشده است.

### CDI
- محیط هدف: isolated staging
- Docker stack طراحی شده: PostgreSQL + Redis + Django/Gunicorn + Celery worker + Celery beat + Next.js
- پورت‌های داخلی پیشنهادی CDI: backend 127.0.0.1:8001 و frontend 127.0.0.1:3001
- live deployment روی سرور در این مرحله تأیید نشده است.

## 📦 پیشرفت بخش‌ها

| بخش | پیشرفت | باقی‌مانده | وضعیت |
|---|---:|---:|---|
| Foundation | 100% | 0% | ✅ |
| P1 Core Data Engine | 100% | 0% | 🔄 PR |
| Safe Fetch / Provenance | 88% | 12% | 🔄 |
| Normalization / Fingerprint | 90% | 10% | 🔄 |
| Dedup / Review | 88% | 12% | 🔄 |
| Observation / Change | 88% | 12% | 🔄 |
| Export | 85% | 15% | 🔄 |
| Scraper / Celery | 82% | 18% | 🔄 |
| Gardasil real-market benchmark | 55% | 45% | 🔄 |
| Pharmacy / Geography | 30% | 80% | ⏳ |
| Explorer API | 60% | 40% | 🔄 |
| RTL UI | 15% | 85% | ⏳ |
| Isolated Staging | 35% | 65% | 🔄 |
| Production deployment | 0% | 100% | ⏳ |

## 🧪 داده واقعی بازار ایران

Benchmark مرجع: Gardasil 9 در Pillix.

نمونه‌های واقعی بررسی‌شده:
- https://pillix.ir/medicine/med-mivz
- https://pillix.ir/medicine/med-bhl4

هدف benchmark:
1. Fetch واقعی
2. Raw capture
3. Extraction واقعی
4. Persian normalization
5. Fingerprint
6. Canonical identity
7. Observation
8. Dedup candidate
9. Dry-run rollback
10. Persist
11. Idempotency در اجرای مجدد

هیچ fixture یا رکورد ساختگی برای acceptance بازار استفاده نمی‌شود.

## 🔐 وضعیت امنیت

- robots-aware fetching
- source-domain enforcement
- redirect خارج از دامنه قبل از DNS/public-IP validation رد می‌شود
- public-IP / SSRF protection
- response-size limit
- rate limiting
- authentication/RBAC پایه
- write API محدود به staff
- Production isolation

## 📝 تصمیمات کلیدی

### 2026-09-20 — Domain-first redirect validation
Redirect مقصد ابتدا باید از نظر source-domain مجاز بررسی شود و سپس DNS/public-IP validation انجام شود. دلیل: جلوگیری از cross-domain redirect و SSRF ناخواسته.

### 2026-09-20 — Dedup threshold
Threshold کشف candidate روی 0.6500 قرار گرفت تا رکوردهای sparse واقعی 2/3 matching از candidate discovery حذف نشوند. این threshold به معنی merge خودکار نیست.

### 2026-09-20 — Pharmacy فاز بعد
Pharmacy و MarketObservation قبل از acceptance واقعی Gardasil وارد migration سنگین نمی‌شوند؛ ابتدا قرارداد داده با دو نمونه واقعی تثبیت می‌شود.

### 2026-09-20 — عدم over-engineering
Elasticsearch، Kafka، microservices، ML dedup و browser automation سراسری فعلاً وارد Core نمی‌شوند؛ فقط در صورت نیاز واقعی داده/بار اضافه خواهند شد.

## 🧠 درس‌آموخته‌ها

- تست باید قرارداد واقعی امنیتی سیستم را منعکس کند؛ تست قدیمی redirect با رفتار امن domain-first هم‌خوان نبود.
- قیمت/موجودی observation هستند و نباید به property دائمی محصول تبدیل شوند.
- Gardasil variants مشابه ممکن است identity نزدیک ولی presentation متفاوت داشته باشند؛ dedup نباید به حذف خودکار تبدیل شود.
- روی سرور 2GB/2CPU، worker با concurrency=1 و prefetch=1 انتخاب محافظه‌کارانه و عملی است.
- مستندات وضعیت باید قبل از تغییر کد مرور و بعد از هر مرحله به‌روزرسانی شوند.

## 🔜 مسیر اجرایی بعدی

1. تأیید نتیجه CI مربوط به head واقعی، بدون rerun تکراری.
2. اجرای benchmark واقعی دو صفحه Gardasil روی isolated CDI stack.
3. بررسی rollback واقعی و سپس persist.
4. اجرای مجدد برای idempotency و observation/change.
5. پیاده‌سازی حداقلی و واقعی Pharmacy + Location + MarketObservation.
6. crawl محدود واقعی تهران/Gardasil.
7. تکمیل Explorer API روی داده واقعی.
8. ساخت RTL Explorer واقعی، نه mock.
9. staging کامل با resource limits و backup/restore.
10. سپس تصمیم درباره deployment به Production؛ بدون تغییر Production قبل از acceptance staging.

## 🚫 وضعیت‌های ممنوع

- تغییر Foundation بدون تصمیم صریح
- merge خودکار PR
- تغییر سرویس‌های موجود Cofinets
- docker compose down روی shared production stack
- docker system prune
- broad firewall changes
- bypass CAPTCHA/login/paywall/security
- داده fake برای acceptance
- اعلام Done بدون اجرای واقعی


## 🧪 آخرین اصلاح CI — 2026-09-20

CI head `6540ce7` در مرحله `makemigrations --check --dry-run` شکست خورد و Django migration جدید `0011` برای rename شش index پیشنهاد کرد. علت، استفاده از indexهای بدون نام صریح در models در کنار نام‌های تولیدشده داخل migration `0010` بود. در head `f3affe3` نام indexهای مدل با migration موجود تثبیت شد؛ هیچ migration جدیدی عمداً ایجاد نشده است. نتیجه CI برای headهای جدید هنوز در API مشاهده نشده است و نباید PASS فرض شود.

## 🏥 به‌روزرسانی فاز Pharmacy

در PR فعال، مدل‌های Pharmacy و MarketObservation، migration 0010 و endpointهای API اضافه شده‌اند. این مرحله بر اساس ساختار واقعی صفحات داروخانه Pillix طراحی شده است. این کد هنوز merge/deploy نشده و acceptance آن باید با migration/CI و crawl واقعی isolated انجام شود.


## 2026-09-20 — Structured extraction hardening

در بازبینی عمیق پس از خطای CI، یک ایراد عملکردی مستقل نیز پیدا و اصلاح شد: مسیر `execute_many()` فقط `fields` را به extractor می‌داد و بنابراین `label_table` و `regex_fields` که برای benchmark واقعی Gardasil تعریف شده بودند در اجرای paginated اعمال نمی‌شدند. اصلاح در head `3d047d0` و تست regression در `b398626` انجام شد. head فعلی شاخه P1 پس از مستندسازی `a80761e` است.


## 2026-09-20 — 12:38 +03:30 — ادامه اجرای P1 و همگام‌سازی وضعیت

- PR #1: Open / Draft / Not Merged
- Active branch: cdi-v1-p1-core-data-engine
- Latest head: 65040114966fc673cf46f12d7fb0da160a2d63e7
- CI این head: چهار workflow اصلی SUCCESS شدند: Backend, Backend Docker, Frontend Docker, Compose Integration.
- اصلاحات: Generic JSON-LD Product matching؛ هم‌راستاسازی Source Adapter catalog با Registry؛ اتصال bounded discovery به اجرای Adapter و گزارش extraction.

### برآورد مهندسی فعلی
- کل پروژه: 76% انجام / 24% باقی‌مانده
- Foundation: 100/0
- P1 Core Data Engine: 100/0 (در PR)
- Safe Fetch / Provenance: 88/12
- Normalization / Fingerprint: 90/10
- Dedup / Review: 90/10
- Observation / Change: 50/50
- Structured Extraction: 92/8
- Multi-source Discovery: 70/30
- Multi-source Parsing: 45/55
- Pharmacy / Geography: 55/45
- Real Pharmacy Crawl: 35/65
- Gardasil real-market benchmark: 60/40
- Explorer API: 60/40
- RTL UI: 15/85
- Isolated Staging: 42/58
- Production: 0/100

این درصدها شاخص مدیریت فاز هستند و Done بودن Production را ادعا نمی‌کنند.

### فعالیت این مرحله
1. فایل‌های مرجع پروژه مرور شدند.
2. CI head 6504011 بدون rerun غیرضروری بررسی شد و هر چهار workflow موفق بودند.
3. ایراد واقعی Generic JSON-LD در تشخیص Product اصلاح شد.
4. Discovery پس از Fetch موفق Adapter همان Source را اجرا و تعداد رکوردهای استخراج‌شده را گزارش می‌کند.
5. catalog با Adapterهای موجود Registry هم‌راستا شد.
6. هیچ تغییر Production انجام نشد.

### داده واقعی بازار
Benchmark بازار باید چندمنبعی باشد. Pillix برای اطلاعات دارویی یک منبع عمومی واقعی است. مقدار قیمت نمایش‌داده‌شده 0 به‌صورت قیمت واقعی پذیرفته نمی‌شود تا معنای آن اثبات شود.

### گام بعدی
اتصال خروجی Adapter به process_records() و سپس benchmark واقعی چندمنبعی Gardasil، با تفکیک محصول/دارو/فروشنده/داروخانه و observation؛ سپس pharmacy crawl، Explorer API، RTL Explorer و isolated staging.

### قاعده پذیرش
یک URL به‌تنهایی معیار پذیرش CDI نیست؛ پذیرش بازار باید روی چند domain مستقل و Adapterهای متناسب با ساختار هر Source انجام شود.


## 2026-09-20 — 12:58 +03:30 — Adapter → Data Pipeline integration

### وضعیت واقعی
- head پس از این مرحله: ae1205e5e0f5f7e7d5726499022c67cf807e270a
- خروجی Adapter اکنون به قرارداد `datahub.pipeline.process_records()` متصل شده است.
- برای extraction عمومی، EntityType/fields حداقلی `product` به‌صورت idempotent ایجاد می‌شوند.
- `RawCapture` موفق، `source_domain`، URL، evidence و شناسه capture همراه رکورد/observation حفظ می‌شوند.
- captureهای blocked/error وارد pipeline نمی‌شوند.
- حالت پیش‌فرض command همچنان rollback کامل دارد؛ `--persist` تنها مسیر commit است.
- regression test برای provenance و observation اضافه شد.
- CI برای این head هنوز اجرا/تأیید نشده است؛ بنابراین PASS ادعا نمی‌شود.
- Production هیچ تغییری نکرده است.

### اصلاح مهم قراردادی
Adapter output دیگر فقط برای شمارش extraction استفاده نمی‌شود؛ اکنون:
`Fetch → RawCapture → Adapter → adapter_record_to_item → process_records → ExtractedRecord → RecordObservation`

### محدودیت آگاهانه
این مرحله هنوز acceptance بازار Gardasil نیست. Adapter عمومی فقط زمانی رکورد Product می‌سازد که evidence ساختاری معتبر داشته باشد. مرحله بعد باید با URLهای واقعی و چند دامنه مستقل، استخراج و semantics هر source را جداگانه اثبات کند.

### گام بعدی مستقیم
1. CI جدید را فقط یک بار بررسی می‌کنیم.
2. سپس benchmark واقعی Gardasil چندمنبعی را روی محیط isolated اجرا می‌کنیم.
3. قیمت/موجودی را observation نگه می‌داریم و مقدار مبهم `0` را قیمت واقعی فرض نمی‌کنیم.
4. پس از acceptance، Pharmacy/MarketObservation و crawl محدود تهران را به pipeline متصل می‌کنیم.


## 2026-09-20 — 13:06 +03:30 — Multi-source Gardasil benchmark sources registered

- منابع واقعی مستقل برای benchmark اضافه شدند:
  - Pillix — اطلاعات دارویی/رگولاتوری عمومی
  - Iran Supplement — صفحات تجاری Gardasil 9 با قیمت
  - PharmaWeb — صفحات تجاری Gardasil 9 با قیمت، موجودی و شناسه محصول
- این صفحات فقط seed هستند؛ acceptance زمانی معتبر است که Fetch واقعی + Adapter + persistence روی چند domain مستقل اجرا و نتیجه مشاهده شود.
- Iran Supplement و PharmaWeb فعلاً با adapter عمومی JSON-LD ثبت شده‌اند؛ اگر HTML/semantic evidence واقعی نشان دهد که کافی نیست، adapter اختصاصی همان source اضافه می‌شود.
- اطلاعات تجاری به‌عنوان observation بازار ثبت می‌شود و جایگزین حقیقت رگولاتوری نیست.
- قیمت Pillix که `0` نمایش داده می‌شود به‌صورت قیمت واقعی parse/interpret نمی‌شود.
- آخرین head فعلی: `1c514886997fb38692eb3f011710a160e0c4df52`
- CI برای این head هنوز نتیجه‌ای گزارش نکرده است.


## 2026-09-20 — Pharmacy adapter → pipeline integration

- Latest head: `fa6b3ce1918bfbb9cd6d85a77e40c0166609e848`
- CI on the previous head `1fd2834` is verified: Backend, Backend Docker, Frontend Docker and Compose Integration all completed successfully.
- Pillix now uses source-specific routing: `/pharmacy/` pages are parsed by `pillix_pharmacy`; other Pillix pages keep the generic adapter.
- Pharmacy adapter output now follows the same provenance path:
  `RawCapture → adapter → adapter_record_to_item → process_records → ExtractedRecord/RecordObservation → Pharmacy/Location`.
- A dedicated `pharmacy` EntityType contract was added to the discovery command with required geographic identity fields; materialization uses the existing `upsert_pharmacy_from_record()` path and does not infer drug availability.
- Discovery output now reports `pharmacies_materialized` per capture/source.
- Regression coverage added for source-specific adapter routing and explicit Pillix pharmacy-card extraction.
- No new database migration was introduced; existing Pharmacy/Location schema is reused.
- This is still an isolated PR branch. No production server changes or live staging execution are claimed.
- Real pharmacy acceptance remains pending until an isolated environment can execute the command against the actual Pillix pages.

### Engineering estimate after this block

- Overall: **~79% complete / ~21% remaining**
- Pharmacy / Geography: **~70% / ~30%**
- Real Pharmacy Crawl: **~45% / ~55%**
- Multi-source Parsing: **~50% / ~50%**
- Gardasil real-market benchmark: **~60% / ~40%**
- Observation / Change: **~88% / ~12%**

These are management estimates, not production-completion claims.

### Next execution block

1. Check CI once for the new head `fa6b3ce`; do not rerun unchanged workflows.
2. Run the actual Pillix pharmacy crawl in isolated staging with a small bounded page limit.
3. Verify dry-run rollback, then persist, then repeat for idempotency.
4. Add MarketObservation only after a real pharmacy/product relationship is evidenced by source data; do not infer availability from a pharmacy directory page.
5. Run the multi-domain Gardasil benchmark and inspect source-specific semantics.


## 2026-09-20 — CI verification + per-capture transaction hardening + Pillix pharmacy seed

- Latest verified PR head before this documentation update: `ca3a7bc5b877d4b9da1c0697163c7b75e39022a5`.
- CI for that head is now **PASS** across all four required workflows: Backend, Backend Docker, Frontend Docker and Compose Integration.
- Transaction hardening is implemented in `cdi_source_discovery`: each capture's persistence work is wrapped in an inner `transaction.atomic()` savepoint. This prevents a single database exception from poisoning the surrounding dry-run transaction while preserving the final dry-run rollback contract.
- The Pillix source catalog was strengthened with the real public pharmacy directory root `https://pillix.ir/pharmacy` as an additional seed. The existing province/county pharmacy seeds remain; no seed was removed.
- This seed change is a coverage improvement, not market acceptance. Real isolated crawl is still required to verify extraction, persistence, rollback and idempotency against live Pillix responses.
- Production remains untouched; no live staging execution is claimed.

### Engineering estimate after this block
- Overall: **~80% complete / ~20% remaining**
- Safe Fetch / Provenance: **~90% / ~10%**
- Pharmacy / Geography: **~72% / ~28%**
- Real Pharmacy Crawl: **~45% / ~55%**
- Multi-source Parsing: **~50% / ~50%**
- Gardasil real-market benchmark: **~60% / ~40%**
- Observation / Change: **~88% / ~12%**

These remain management estimates, not production-completion claims.

### Next execution block
1. Use the isolated environment to execute the bounded Pillix pharmacy crawl against the new root seed.
2. Capture actual dry-run output and verify zero durable DB writes.
3. Persist the same bounded crawl and inspect provenance/Location/Pharmacy materialization.
4. Repeat the crawl to verify idempotency without inferring stock or availability.
5. Then run the real multi-domain Gardasil benchmark and only introduce MarketObservation where source evidence explicitly establishes a product/pharmacy relationship.
