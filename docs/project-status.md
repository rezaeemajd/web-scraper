# CDI — Project Status / Continuation Report

> آخرین به‌روزرسانی: 2026-09-20
> این فایل مرجع ادامه پروژه است و قبل از هر تغییر مهم باید مرور شود. Foundation و Production تا اثبات کامل staging دست‌نخورده می‌مانند.

## وضعیت کلان

| بخش | وضعیت | پیشرفت | باقی‌مانده |
|---|---|---:|---:|
| Foundation | سالم/منجمد | 100% | 0% |
| P1 Core Data Engine | Draft PR#1 فعال | 100% | 0% |
| Safe Fetch / Provenance | عملیاتی | 88% | 12% |
| Persian normalization / fingerprint | عملیاتی | 90% | 10% |
| Dedup / review | عملیاتی + hardening | 88% | 12% |
| Observation / change history | عملیاتی | 88% | 12% |
| Export | عملیاتی | 85% | 15% |
| Scraper / Celery | عملیاتی + hardening | 82% | 18% |
| Real Iran benchmark | Gardasil آماده؛ اجرای live سرور باقی | 55% | 45% |
| Pharmacy / geography | طراحی هدف؛ پیاده‌سازی بعدی | 20% | 80% |
| Explorer API | پایه موجود | 60% | 40% |
| RTL UI | ابتدایی | 15% | 85% |
| Isolated staging | در حال آماده‌سازی | 35% | 65% |
| Production | عمداً صفر | 0% | 100% |

**برآورد کل: ~63%**؛ درصدها شاخص مهندسی تقریبی هستند، نه KPI اندازه‌گیری‌شده.

## GitHub

- Repository: rezaeemajd/web-scraper
- Foundation: cdi-v1-foundation @ c072da00dfce2d3c5c27b11c499a73c45343c95b
- P1: cdi-v1-p1-core-data-engine
- PR #1: feat: CDI P1 core data engine — OPEN / DRAFT / NOT MERGED
- آخرین commit branch: 51a155b1c827dafd9234576462a1cc49d606d20d
- force-push/reset/delete نسخه‌ها ممنوع.

## CI و اصلاحات اخیر

آخرین run کامل قبل از hardening: Backend Docker SUCCESS، Frontend Docker SUCCESS، Compose Integration SUCCESS، Backend CI FAILURE با 16 failure / 52 pass.

ریشه خطاها:
1. fake HTTP client تست متد close نداشت.
2. dedup در entityهای بدون blocking metadata صفر candidate می‌داد.
3. DecimalField با string مقایسه می‌شد.
4. task adapter دو-تایی pages_fetched را از captures محاسبه نمی‌کرد.

اصلاح شده:
- bounded fallback برای dedup blocking
- محاسبه pages_fetched از captureها
- lifecycle کامل fake HTTP client
- مقایسه Decimal با Decimal

**آخرین CI برای head قبلی هنوز 4 failure داشت (64 pass). هر 4 مورد root-cause بررسی شد؛ اصلاحات جدید روی head فعلی اعمال شده و اجرای CI جدید هنوز در GitHub ظاهر نشده است.**

## اصلاحات آخر این مرحله

- dedup اکنون در نبود metadata بلاکینگ، fallback محدود از payload دارد و از zero-candidate خاموش جلوگیری می‌کند.
- extraction موتور اکنون label-table و regex field را پشتیبانی می‌کند؛ بنابراین ساختار واقعی جدول‌های Pillix مستقیماً قابل استخراج است.
- API list pagination اکنون ordering پایدار دارد و warningهای QuerySet unordered رفع شده‌اند.
- benchmark پیش‌فرض به دو صفحه واقعی Gardasil 9 گسترش یافته است: med-mivz و med-bhl4.
- این دو variant عمداً برای سنجش identity در برابر duplicate استفاده می‌شوند؛ تفاوت تولیدکننده/کشور/بسته‌بندی نباید به collapse خودکار منجر شود.

## CI: آخرین root-cause analysis

Run 35496176579 روی head قبلی: migration و makemigrations سالم بودند؛ 64 تست pass و 4 تست fail شدند. دو failure مربوط به dedup به threshold 0.70 در رکوردهای sparse برمی‌گشت؛ threshold عملیاتی برای candidate discovery به 0.65 تنظیم و تست symmetry اضافه شد. یک failure مربوط به ترتیب redirect بود: قبل از DNS، cross-domain باید reject شود؛ ترتیب امن اصلاح شد. یک failure مربوط به mock اشتباه rate-limit بود؛ تست اکنون semantics واقعی fixed-window را مدل می‌کند (cache.add=false و increment بالاتر از limit). سه warning pagination نیز با ordering صریح API اصلاح شد.

## Benchmark واقعی بازار ایران

منبع اصلی: Pillix، صفحه واقعی Gardasil 9:
https://pillix.ir/medicine/med-mivz

صفحه واقعی دوم:
https://pillix.ir/medicine/med-bhl4

صفحه اول فعلاً Gardasil 9، صاحب پروانه بهستان دارو، تولیدکننده MSD، کشور ایرلند، ATC J07BM03 و بسته 1 سرنگ در 1 جعبه را نشان می‌دهد. صفحه دوم همان خانواده را با تولیدکننده Merck Sharp & Dohme، کشور آمریکا و بسته 1 ویال در 1 جعبه نشان می‌دهد.

این دو صفحه برای identity/dedup benchmark ارزش واقعی دارند: شباهت بالا نباید باعث collapse خودکار دو variant واقعی شود.

Pillix اطلاعات را از سامانه اطلاعات دارویی کشور معرفی می‌کند ولی مسئولیت صحت را نمی‌پذیرد؛ CDI باید provenance را نگه دارد و drug information را با pharmacy stock یا وضعیت قانونی یکی نکند.

## معماری تثبیت‌شده

Source -> Safe Fetch -> RawCapture/SHA256 -> Parser -> Persian normalization -> fingerprint/identity -> ExtractedRecord -> Observation/Change -> Dedup -> API/Export

قواعد بازار:
Drug information != Pharmacy availability
Pharmacy availability != Current stock
Current stock != Legal/import status
Market price != ویژگی ثابت محصول

Availability/price/stock باید observation زمان‌دار و متصل به pharmacy/location/source باشند.

## رویکرد فنی

Django + PostgreSQL + Redis + Celery + HTTPX + Selectolax/Lexbor؛ bounded fetch، robots/domain/private-network safety، JSONB blocking + similarity، سقف candidate scan، transaction.atomic، Celery retry فقط برای transient، export کم‌حافظه. از abstraction پیچیده و crawler framework غیرضروری پرهیز می‌شود.

## ترتیب ادامه

1. یک بار CI جدید را بررسی و failure واقعی را root-cause fix کنیم.
2. روی isolated CDI stack: benchmark دو صفحه واقعی Gardasil را dry-run و سپس persist کنیم.
3. مقایسه واقعی دو صفحه Gardasil و identity/dedup.
4. extraction ساختاری manufacturer/country/licence/package/ATC/price با evidence.
5. Pharmacy + Location + MarketObservation.
6. crawl محدود واقعی pharmacyهای مرتبط و city/province.
7. idempotency/change واقعی.
8. Explorer API.
9. RTL Persian UI.
10. bounded staging crawl و rollback validation.
11. فقط پس از اثبات staging، Production.

## قواعد سخت

Production/Cofinets/Nginx دستکاری نشود؛ Foundation merge نشود تا acceptance کامل و تصمیم صریح؛ market benchmark فقط با داده واقعی؛ live crawl bounded و rate-limited؛ تست تکراری بی‌هدف ممنوع؛ هر تغییر مهم در همین فایل ثبت شود.
