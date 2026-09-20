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
- آخرین commit branch: `21103f00441ff6c4edaef49b794dcf65b5e5f714` (Pharmacy materialization + tests)
- force-push/reset/delete نسخه‌ها ممنوع.

## CI و اصلاحات اخیر

آخرین CI تأییدشده روی head `5f8d91b309e46ad51313b3091d92dbd7300f7d91`: Backend Docker SUCCESS، Frontend Docker SUCCESS، Backend CI SUCCESS، Compose Integration SUCCESS. چهار workflow سبز هستند.

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

**CI فعلی سبز است.** چهار workflow مربوط به head `5f8d91b` با موفقیت کامل شده‌اند؛ بنابراین gate مربوط به migration/index naming و regressionهای اخیر بسته شده است.

## اصلاحات آخر این مرحله

- dedup اکنون در نبود metadata بلاکینگ، fallback محدود از payload دارد و از zero-candidate خاموش جلوگیری می‌کند.
- extraction موتور اکنون label-table و regex field را پشتیبانی می‌کند؛ بنابراین ساختار واقعی جدول‌های Pillix مستقیماً قابل استخراج است.
- API list pagination اکنون ordering پایدار دارد و warningهای QuerySet unordered رفع شده‌اند.
- benchmark پیش‌فرض به دو صفحه واقعی Gardasil 9 گسترش یافته است: med-mivz و med-bhl4.
- این دو variant عمداً برای سنجش identity در برابر duplicate استفاده می‌شوند؛ تفاوت تولیدکننده/کشور/بسته‌بندی نباید به collapse خودکار منجر شود.

## CI: آخرین root-cause analysis

Run 35496176579 روی head قبلی: migration و makemigrations سالم بودند؛ 64 تست pass و 4 تست fail شدند. دو failure مربوط به dedup به threshold 0.70 در رکوردهای sparse برمی‌گشت؛ threshold عملیاتی برای candidate discovery به 0.65 تنظیم و تست symmetry اضافه شد. یک failure مربوط به ترتیب redirect بود: قبل از DNS، cross-domain باید reject شود؛ ترتیب امن اصلاح شد. یک failure مربوط به mock اشتباه rate-limit بود؛ تست اکنون semantics واقعی fixed-window را مدل می‌کند (cache.add=false و increment بالاتر از limit). سه warning pagination نیز با ordering صریح API اصلاح شد.

## تصمیم مهندسی برای سرعت پروژه

CI اکنون سبز است؛ بنابراین Pharmacy/MarketObservation روی همین PR branch قابل ادامه است. اما پذیرش این فاز هنوز به اجرای benchmark واقعی روی isolated stack و crawl محدود واقعی وابسته است؛ Foundation و Production همچنان دست‌نخورده می‌مانند.

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


## فاز Pharmacy + MarketObservation — شروع شده

بر اساس ساختار واقعی صفحات Pillix، Pharmacy به‌صورت مستقل از Product طراحی شد. مدل Pharmacy شامل نام، Location، منبع، URL، نوع، ساعات، تلفن عمومی، وب‌سایت و evidence است. MarketObservation به Pharmacy + ExtractedRecord + RawCapture متصل است و availability/price را به‌صورت observation زمانی نگه می‌دارد؛ موجودی دائمی روی Product ثبت نمی‌شود.

پیاده‌سازی فعلی در PR branch انجام شده و شامل model، migration 0010، serializer و endpointهای API است. قبل از پذیرش نهایی باید migration/CI و سپس crawl واقعی isolated اجرا شود.


## 2026-09-20 — CI root-cause fix + structured extraction hardening

- CI on head `6540ce7` reached the migration consistency gate and failed because Django generated six index-renaming operations for Pharmacy/MarketObservation.
- Root cause: `0010_pharmacy_market_observation.py` contained stable generated index names while the models declared the same indexes without explicit names.
- Fixed on head `f3affe3` by explicitly pinning those six model index names to the migration names; no extra migration was introduced.
- During code review of the same path, a real extraction bug was found: `execute_many()` passed only CSS `fields` into `_extract_payload()`, silently dropping configured `label_table` and `regex_fields`.
- Fixed on head `3d047d0` and added a regression test on head `b398626` covering label-table and regex extraction through the actual paged execution path.
- The next CI result must validate both fixes; no CI rerun was manually triggered.


## 2026-09-20 — Second CI root cause

CI head `a80761e` completed. Backend Docker and Frontend Docker passed, while Backend and Compose Integration failed at Django system checks during migration. Exact root cause: the six explicit Pharmacy/MarketObservation index names were still longer than Django's 30-character model index-name limit. This was a naming issue, not a database/data issue.

Fixed without adding another migration: `models.py` and the still-unmerged `0010_pharmacy_market_observation.py` now use stable names under 30 characters:
- `pharm_src_name_idx`
- `pharm_loc_active_idx`
- `mktobs_record_time_idx`
- `mktobs_pharm_time_idx`
- `mktobs_source_time_idx`
- `mktobs_avail_time_idx`

The migration remains pre-merge and therefore safe to correct in place. New head: `c38a638`.


## 2026-09-20 — CI سبز + Pharmacy materialization

- Head `5f8d91b309e46ad51313b3091d92dbd7300f7d91` اکنون چهار workflow را با موفقیت گذرانده است: Backend CI، Backend Docker CI، Frontend Docker CI و Compose Integration CI.
- نتیجه: root cause مربوط به نام indexهای migration بسته شد و regression مربوط به structured extraction نیز در مسیر CI تأیید شد.
- اقدام بعدی دیگر CI نیست: اجرای واقعی benchmark دو صفحه Gardasil روی isolated CDI stack و سپس بررسی idempotency، fingerprint/identity و dedup candidate است.
- دسترسی اجرای زنده به سرور در این جلسه در دسترس نیست؛ بنابراین هیچ اجرای live یا نتیجه دیتابیسی ادعا نمی‌شود. پس از فراهم شدن اجرای isolated، همان benchmark واقعی بدون fixture ساختگی اجرا خواهد شد.
- Pharmacy/MarketObservation پیاده‌سازی شده ولی هنوز market-accepted نیست؛ پذیرش آن منوط به داده واقعی pharmacy و evidence محصول-داروخانه است.


## 2026-09-20 — Pharmacy materialization hardening

- Head `b70c113351272f1a3c7612a78ae0a1f5ac73d5cc` اکنون چهار workflow را سبز گذرانده است: Backend CI، Backend Docker CI، Frontend Docker CI و Compose Integration CI.
- پس از بسته‌شدن gateهای CI، یک لایه کوچک و غیرتهاجمی برای تبدیل `ExtractedRecord` داروخانه به `Pharmacy + Location` اضافه شد: `backend/datahub/pharmacy_pipeline.py`.
- سرویس `upsert_pharmacy_from_record()` بر اساس `source_domain + source_url` upsert می‌کند، Location را از province/city/district/address می‌سازد، evidence/provenance را نگه می‌دارد و هیچ `MarketObservation` یا موجودی محصولی را از صرفاً وجود داروخانه استنتاج نمی‌کند.
- دو تست regression برای materialization و idempotency اضافه شد: `backend/datahub/test_pharmacy_pipeline.py`.
- commitهای جدید بعد از CI سبز هستند؛ بنابراین این دو commit هنوز باید یک بار از CI عبور کنند. تا قبل از نتیجه جدید، سبز بودن آن‌ها ادعا نمی‌شود.
- این مرحله هنوز crawl واقعی pharmacy نیست. قدم بعدی: adapter/selector محدود Pillix برای استخراج رکوردهای واقعی داروخانه، سپس اجرای crawl یک صفحه/حداکثر چند صفحه در isolated staging و بررسی Location dedup + Pharmacy upsert.


## 2026-09-20 — Pillix pharmacy adapter

- CI چهارگانه برای commit `2ffed6091078d462ad269ebbf7ce0623d7b7e674` سبز شد.
- parser مستقل `backend/scraping/adapters/pillix_pharmacy.py` اضافه شد. parser بر اساس داده‌های صریح کارت داروخانه (`h2`, استان، شهرستان، آدرس و نوع فعالیت) کار می‌کند و availability را استنتاج نمی‌کند.
- parser pure و قابل تست است و duplicate cardهای یکسان را حذف می‌کند.
- تست‌های adapter در `backend/scraping/adapters/test_pillix_pharmacy.py` اضافه شدند.
- این مرحله هنوز crawl شبکه‌ای یا persistence را فعال نمی‌کند؛ بنابراین ریسک production ندارد. قدم بعدی اتصال adapter به pipeline اجرای scraper و اجرای bounded crawl واقعی در staging است.
