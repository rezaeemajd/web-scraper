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
- آخرین head شناخته‌شده PR: 6c9013e41c52c5283b0a66953e7603c48f7df344
- PR mergeable: در آخرین بررسی GitHub، true
- CI: اجرای موفق نهایی برای آخرین head مستند نشده؛ بنابراین PASS نهایی اعلام نمی‌شود.
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


## 🏥 به‌روزرسانی فاز Pharmacy

در PR فعال، مدل‌های Pharmacy و MarketObservation، migration 0010 و endpointهای API اضافه شده‌اند. این مرحله بر اساس ساختار واقعی صفحات داروخانه Pillix طراحی شده است. این کد هنوز merge/deploy نشده و acceptance آن باید با migration/CI و crawl واقعی isolated انجام شود.
