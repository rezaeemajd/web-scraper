
MASTER PROMPT

COFINETS WEB DATA INTELLIGENCE & SCRAPER PLATFORM

نقش تو

تو یک تیم کامل و Senior در حوزه‌های زیر هستی:

Senior Python Developer

Senior Django Developer

Senior Frontend Developer

Web Data Engineer

Web Scraping Architect

Data Pipeline Engineer

Database Architect

Linux/Docker/DevOps Engineer

Security Engineer

UI/UX Designer

QA Engineer

Data Quality Engineer

وظیفه تو ایجاد یک Production-Ready Web Data Acquisition, Scraping & Market Intelligence Platform است.

این سیستم باید واقعاً قابل اجرا، قابل توسعه، قابل نگهداری و قابل استقرار روی Linux Server باشد.

این پروژه فقط یک Script ساده Python نیست.

باید یک Web Application کامل با:

Backend

Frontend

Admin

Authentication

RBAC

Scraper Engine

Scheduler

Data Pipeline

Parser Engine

Export Engine

Data Cleaning

Deduplication

Monitoring

Logging

Reports

API

Docker

PostgreSQL

Redis

Celery

Nginx

Backup

Restore

Documentation

Tests

ایجاد شود.

نام پروژه

نام:

Cofinets Data Intelligence

نام کوتاه:

CDI

دامنه:

https://cofinets.com

این پروژه باید از پروژه‌های فعلی Cofinets کاملاً جدا و Non-Destructive باشد.

هدف اصلی

هدف سیستم:

جمع‌آوری، پاک‌سازی، نرمال‌سازی، طبقه‌بندی و تحلیل داده‌های عمومی وب.

تمرکز اولیه:

Healthcare / Medical / Pharmaceutical

داده‌های اولیه:

داروها

داروهای پرمصرف

داروهای کمیاب

داروهای پرتقاضا

داروهای فصلی

برندها

نام ژنریک

شرکت تولیدکننده

کشور تولید

مشخصات محصول

بسته‌بندی

وضعیت موجودی در منابع عمومی

اطلاعات قیمت در صورت عمومی بودن

منابع مرتبط

داروخانه‌ها

نام

استان

شهر

منطقه

آدرس

تلفن ثابت عمومی

شماره تماس سازمانی عمومی

وب‌سایت

شبکه‌های اجتماعی عمومی

ساعات فعالیت در صورت عمومی بودن

اطلاعات مکانی عمومی

منبع

تاریخ آخرین بررسی

پزشکان / مطب‌ها

نام

تخصص

شهر

استان

آدرس کاری عمومی

شماره تماس کاری عمومی

وب‌سایت

شبکه اجتماعی عمومی

منبع

تاریخ بررسی

کلینیک‌ها

نام

نوع

تخصص

استان

شهر

منطقه

آدرس

تلفن

وب‌سایت

شبکه‌های اجتماعی عمومی

خدمات

منبع

اصل مهم

این سیستم برای:

جمع‌آوری داده عمومی و مجاز

طراحی می‌شود.

نباید برای موارد زیر ساخته شود:

دور زدن CAPTCHA

دور زدن Login

شکستن محدودیت دسترسی

Bypass کردن Paywall

دور زدن مکانیزم‌های امنیتی

استخراج اطلاعات خصوصی

جمع‌آوری اطلاعاتی که عمداً خصوصی نگه داشته شده‌اند

استفاده از حساب کاربری دیگران

حمله به سایت‌ها

سیستم باید Rate Limit و احترام به قوانین هر Source داشته باشد.

Architecture

Architecture:

INTERNET | NGINX | WEB APPLICATION | +---------+---------+ | | FRONTEND BACKEND | +------------+------------+ | | | PostgreSQL Redis Storage | Celery Worker | Scraper Engine | +------------+-------------+ | | | HTTP Browser API Fetcher Fetcher Source | | | +------------+-------------+ | Parser Engine | Normalization | Deduplication | Data Validation | Data Store | Export / API 

تکنولوژی

Backend:

Python 3.13+
Django
Django REST Framework
Celery
Redis
PostgreSQL

Scraping:

httpx / requests
BeautifulSoup
lxml
selectolax

برای صفحات JavaScript در صورت نیاز:

Playwright

اما Browser automation فقط زمانی استفاده شود که واقعاً لازم است.

از Browser برای تمام سایت‌ها استفاده نکن.

Frontend

ترجیحاً:

Next.js
React
TypeScript
Tailwind CSS

Frontend:

RTL

فارسی

Responsive

Mobile Friendly

Desktop Friendly

Dark/Light آماده

Modern UI

Dashboard-oriented

Database

PostgreSQL.

مدل‌های اصلی:

Source
SourceCategory
Scraper
ScraperMethod
ScraperRun
ScraperTask
RawPage
RawDocument
ExtractedRecord
NormalizedRecord
Entity
EntityType
FieldDefinition
FieldValue
Location
Province
City
District
Address
Phone
SocialAccount
Brand
Product
Organization
Person
Pharmacy
Clinic
Doctor
Office
Supplier
Tag
DataSource
DataQualityScore
DuplicateCandidate
ChangeHistory
ExportJob
ExportFile
User
Role
Permission
AuditLog

Generic Data Model

سیستم نباید از ابتدا فقط برای Pharmacy ساخته شود.

Entity system باید Generic باشد.

مثلاً:

EntityType:
Product
Drug
Pharmacy
Doctor
Clinic
Hospital
Company
Store
Supplier
Manufacturer

در آینده بتوان:

AutoParts
Bearing
ElectricalProduct
ATM
MedicalEquipment
MotorOil
Antifreeze
Octane
IndustrialEquipment

را اضافه کرد.

بدون تغییر اساسی در Core.

Geographic Structure

موقعیت مکانی باید Hierarchical باشد:

Country
└── Province
└── City
└── District
└── Address

برای ایران:

ایران
├── آذربایجان غربی
│ ├── ماکو
│ ├── ارومیه
│ └── ...
├── تهران
├── آذربایجان شرقی
└── ...

Location Normalization

سیستم باید اختلاف نوشتاری را نرمال کند:

ي → ی
ك → ک
ۀ → ه

همچنین:

تهران
تهران،
Tehran
TEHRAN

را تا حد امکان Normalize کند.

Phone Normalization

شماره‌ها باید:

تشخیص داده شوند

نرمال شوند

Country Code تشخیص داده شود

Duplicate شوند یا نشوند

نوع مشخص داشته باشند

مثلاً:

Mobile
Landline
Fax
WhatsApp
Telegram
BusinessPhone
Unknown

اما سیستم نباید صرفاً از روی یک شماره حدس بزند که WhatsApp یا Telegram فعال است.

اگر منبع صریحاً آن را معرفی کرده باشد:

verified_source

ثبت شود.

Social Data

مدل:

SocialAccount

Provider:

Instagram
Telegram
WhatsApp
Facebook
X
LinkedIn
Eitaa
Bale
Rubika
Website
YouTube

Fields:

platform
username
url
display_name
source
verified
last_seen

Data Provenance

هر داده باید بداند از کجا آمده.

مثلاً:

Source:
example.com

URL:
https://example.com/page

Collected At:
2026-09-18

Parser:
pharmacy_parser_v2

Confidence:
0.92

هیچ Record مهمی بدون Source ایجاد نشود مگر اینکه کاربر دستی وارد کرده باشد.

Source Management

Admin بتواند Source جدید اضافه کند.

مثلاً:

Source Name
Domain
Base URL
Source Type
Country
Category
Allowed
Rate Limit
Priority
Notes
Active

Source Types

Website
Directory
Search Result
Public API
RSS
Sitemap
CSV
JSON
XML
PDF
Manual

Scraper Definition

هر Scraper یک Entity مستقل باشد.

مثلاً:

Scraper:
Pharmacy Finder

Fields:

name
slug
description
source
entity_type
status
priority
schedule
method
parser
normalizer
validator
export_profile

Scraper Methods

سیستم باید چند Method داشته باشد.

Method 1

Static HTML.

HTTP
↓
HTML
↓
Parser

Method 2

JSON endpoint عمومی.

HTTP
↓
JSON
↓
Parser

Method 3

XML/RSS.

Method 4

Sitemap.

Method 5

PDF public documents.

Method 6

JavaScript rendered page.

Playwright
↓
DOM
↓
Parser

Method 7

Public API.

Method 8

Search discovery.

اما Search Engine Scraping باید مطابق قوانین و محدودیت‌های سرویس مربوطه باشد؛ در صورت وجود API رسمی، API ترجیح داده شود.

Scraper Builder

Admin باید بتواند Scraper جدید بسازد.

فرم:

Scraper Name
Source
Entity Type
Method
URL
Pagination
Parser
Fields
Filters
Schedule
Rate Limit
Retry
Output

Extraction Methods

سیستم باید Extraction Strategyهای مختلف داشته باشد:

CSS Selector
XPath
JSON Path
Regex
Attribute Extraction
Text Extraction
Link Extraction
Table Extraction
Meta Extraction
Schema.org Extraction
OpenGraph Extraction

Field Mapper

مهم‌ترین قسمت UI:

Admin بتواند:

Source Field
↓
Target Field

تعریف کند.

مثلاً:

نام مرکز
↓
organization.name

یا:

تلفن
↓
phones[]

Parser Pipeline

هر Scraper:

Fetch
↓
Raw Capture
↓
Parse
↓
Field Extraction
↓
Normalization
↓
Validation
↓
Deduplication
↓
Quality Score
↓
Save

Multi-Step Scraping

باید امکان Pipeline چندمرحله‌ای باشد.

مثلاً:

STEP 1
Find category pages

↓

STEP 2
Extract product links

↓

STEP 3
Open product pages

↓

STEP 4
Extract product details

↓

STEP 5
Normalize

↓

STEP 6
Deduplicate

↓

STEP 7
Save

Single-Step Scraping

برای Sourceهای ساده:

URL
↓
Extract
↓
Save

امکان Single Step نیز باشد.

Pagination

پشتیبانی از:

?page=2
?page=3

و:

Next Button
Offset
Limit
Cursor
Load More

تا حد امکان.

اگر Pagination مشخص نیست، Admin بتواند روش را انتخاب کند.

Crawl Limits

هر Job باید داشته باشد:

Max Pages
Max Items
Max Depth
Timeout
Rate Limit
Concurrency

Default محافظه‌کارانه باشد.

Rate Limiting

برای هر Domain:

requests_per_second
requests_per_minute
concurrency
delay

قابل تنظیم باشد.

Retry

Retry قابل تنظیم:

max_retries
backoff
retry_status_codes

مثلاً:

429
500
502
503
504

اما Retry نباید باعث فشار روی Source شود.

Robots.txt

در Source configuration:

Respect Robots = ON

به‌صورت پیش‌فرض.

قبل از Crawl در صورت امکان robots.txt بررسی شود.

Domain Safety

هر Source باید Domain مشخص داشته باشد.

Crawler فقط در Domainهای مجاز حرکت کند.

مثلاً:

example.com

نباید به صورت ناخواسته وارد:

other-domain.com

شود.

URL Normalization

Normalize:

trailing slash

fragments

tracking parameters

UTM

duplicate query strings

اما پارامترهایی که برای محتوا لازم هستند نباید حذف شوند.

Canonical URL

اگر صفحه:

داشت، ذخیره شود.

Raw Data

قبل از Normalization باید امکان ذخیره Raw Response وجود داشته باشد.

اما Storage باید محدود و قابل مدیریت باشد.

مثلاً:

Raw HTML
Raw JSON
Raw PDF

با retention policy.

Data Retention

Admin بتواند تعیین کند:

Raw HTML:
7 days

Raw JSON:
30 days

Parsed Data:
indefinite

مقادیر configurable.

Data Quality

هر Record:

Quality Score

دریافت کند.

بر اساس:

Completeness
Source Reliability
Freshness
Normalization
Validation

Data Validation

Rules:

Phone valid
Email valid
URL valid
Province valid
City valid
Required fields

Duplicate Detection

Duplicate detection باید چند مرحله‌ای باشد.

Exact

URL
Phone
Email
SKU

Normalized

Name + City
Name + Address
Phone + Organization

Fuzzy

در صورت امکان:

Name similarity
Address similarity

اما Fuzzy Match نباید مستقیماً Recordها را حذف کند.

ابتدا:

Duplicate Candidate

ایجاد شود.

Duplicate Review

Admin بتواند:

Merge
Keep Both
Ignore

انتخاب کند.

Data Merge

در Merge:

Sourceها حفظ شوند

تاریخچه حفظ شود

بهترین Field انتخاب شود

Original values قابل مشاهده باشند

Change Detection

اگر Record قبلی:

Phone = X

و اکنون:

Phone = Y

سیستم:

Change Event

بسازد.

Change History

ثبت:

Old Value
New Value
Source
Detected At

Scraper Run

هر اجرا:

ScraperRun

باشد.

اطلاعات:

Started
Finished
Duration
Pages
Items
New
Updated
Duplicates
Errors
Warnings
Status

Run Status

Queued
Running
Paused
Completed
Failed
Cancelled
Partial

Live Monitoring

در Admin:

Current Job
Progress
Pages
Items
Errors
Rate
ETA

در صورت امکان با WebSocket.

Logs

هر Run:

INFO
WARNING
ERROR
DEBUG

داشته باشد.

Error Center

صفحه:

Scraper Errors

با:

Source
URL
Error
Status Code
Parser
Timestamp
Retry

Parser Versioning

هر Parser:

pharmacy_parser_v1
pharmacy_parser_v2

داشته باشد.

تا بتوان Parser جدید را تست و سپس فعال کرد.

Parser Sandbox

Admin بتواند یک URL را وارد کند:

Test URL

و نتیجه:

Raw
Extracted
Normalized
Validation
Final

را ببیند.

Dry Run

قبل از ذخیره واقعی:

DRY RUN

اجرا شود.

مثلاً:

100 pages
500 records

ولی هیچ رکورد نهایی ذخیره نشود.

Sample Run

Admin بتواند فقط:

1 page
5 pages
10 records

را برای تست اجرا کند.

Test Extraction

برای هر Parser:

Test

دکمه داشته باشد.

Field Preview

Admin بتواند نتیجه Fieldها را ببیند:

name
phone
address
city
province
website
social

Selector Helper

در UI امکان وارد کردن:

CSS Selector
XPath
Regex
JSONPath

وجود داشته باشد.

در صورت امکان یک Selector Tester بساز.

Extraction Rules

مثلاً:

name:
CSS .title

phone:
CSS .phone

address:
XPath //div[@class="address"]

website:
CSS a.website @href

Transformation Rules

بعد از Extraction:

Trim
Lowercase
Normalize Persian
Replace
Regex Replace
Split
Join
Parse Phone
Parse URL

Custom Transformation

Admin بتواند Transformation جدید تعریف کند.

اما اجرای کد Arbitrary Python توسط Admin نباید به‌صورت آزاد و بدون Sandbox باشد.

به جای آن:

Predefined transformation operators

طراحی کن.

Advanced Plugin System

برای Developer:

plugins/

داشته باش.

مثلاً:

plugins/pharmacy/
plugins/drug/
plugins/clinic/
plugins/doctor/

هر Plugin:

fetcher
parser
normalizer
validator
exporter

داشته باشد.

Export Engine

خروجی‌ها:

CSV
XLSX
JSON
JSONL
TXT
DOCX
PDF

Excel Export

Excel حرفه‌ای:

Sheets:

Records
Phones
Social
Addresses
Sources
Summary

در صورت مناسب بودن.

Word Export

DOCX:

عنوان

تاریخ

فیلتر

جدول

Source

تعداد رکورد

اطلاعات اصلی

Text Export

مثلاً:

نام:
استان:
شهر:
آدرس:
تلفن:
موبایل:
وب‌سایت:
تلگرام:
واتساپ:
اینستاگرام:
منبع:
تاریخ:

Export Profiles

Admin بتواند Profile بسازد.

مثلاً:

Pharmacy Full
Pharmacy Phone List
Doctors Tehran
Clinics West Azerbaijan
Rare Drugs
Popular Drugs

Filter System

Filters:

Province
City
District
Entity Type
Source
Date
Quality
Status
Brand
Category

Saved Filters

Admin بتواند Filter را ذخیره کند.

مثلاً:

داروخانه‌های تهران

Scheduled Exports

در آینده:

Daily
Weekly
Monthly

قابل اجرا باشد.

User Management

Admin بتواند:

Create User
Edit User
Disable User
Reset Password
Assign Role
Assign Source
Assign Project

Roles

حداقل:

Super Admin
Admin
Scraper Manager
Data Manager
Reviewer
Analyst
Exporter
Viewer

Permissions

Permission granular:

source.view
source.create
source.edit
source.delete

scraper.view
scraper.create
scraper.edit
scraper.run

data.view
data.edit
data.merge
data.delete

export.create
export.download

user.manage
role.manage

Project-Based Access

در آینده:

Project

مثلاً:

Healthcare
Pharmaceutical
Medical Centers
Industrial
Automotive

هر User بتواند فقط Project مشخصی را ببیند.

Admin Dashboard

Dashboard باید شامل:

Total Sources
Active Scrapers
Running Jobs
Records
New Records
Updated Records
Duplicate Candidates
Errors
Exports
Users

باشد.

Geographic Dashboard

نقشه/گزارش:

Province
City
District

و تعداد:

Pharmacy
Clinic
Doctor
Drug

Data Explorer

یک جدول قدرتمند:

Search
Filter
Sort
Column selection
Pagination
Bulk actions
Export

Column Builder

Admin بتواند انتخاب کند چه ستون‌هایی نمایش داده شوند.

Bulk Actions

Tag
Export
Merge
Archive
Review
Delete
Assign

Soft Delete

برای Data Recordهای مهم:

is_deleted
deleted_at
deleted_by

به جای حذف فوری.

Archive

Records قدیمی:

Archive

شوند.

Manual Data Entry

Admin بتواند Record دستی اضافه کند.

مثلاً:

Add Pharmacy
Add Doctor
Add Clinic
Add Product

Manual Verification

Record:

Unverified
Verified
Rejected
Needs Review

Data Review Queue

صفحه:

Needs Review

با:

New Records
Low Quality
Duplicates
Conflicts

Data Conflict

اگر دو Source اطلاعات متفاوت بدهند:

Conflict

بساز.

مثلاً:

Phone A
Phone B

Admin انتخاب کند.

Source Reliability

برای هر Source:

Reliability Score

داخلی.

بر اساس:

Accuracy
Freshness
Completeness
Error rate

Source Health

Dashboard:

Healthy
Warning
Broken
Blocked
Changed Structure

Structure Change Detection

اگر Parser ناگهان:

0 records

برگرداند یا Fieldهای مهم خالی شوند:

هشدار بده.

Alerting

Admin notification:

Parser broken
Source changed
Too many errors
Too many 429
Zero results
Unexpected result drop

Scheduler

Admin بتواند:

Run Now
Every Hour
Every 6 Hours
Daily
Weekly
Cron Expression

تنظیم کند.

Scheduler Safety

دو Job مشابه نباید هم‌زمان روی یک Source اجرا شوند مگر explicitly allowed.

Queue Management

Admin:

Pause
Resume
Cancel
Retry
Retry Failed

داشته باشد.

Scraping Profiles

Profile:

Conservative
Normal
Fast

اما Fast نباید محدودیت‌های Source را نقض کند.

User-Agent

User-Agent واضح و configurable باشد.

مثلاً:

CofinetsDataBot/1.0

و در صورت نیاز Contact URL.

HTTP Headers

Headers قابل تنظیم باشند، اما از جعل هویت یا دور زدن محدودیت‌ها استفاده نشود.

Proxy Architecture

سیستم باید از نظر معماری امکان Proxy داشته باشد.

اما استفاده:

Proxy Pool

فقط برای:

شبکه

پایداری

موقعیت جغرافیایی مجاز

دسترسی عادی

باشد.

نه برای دور زدن محدودیت امنیتی.

Browser Pool

Playwright Browser Pool قابل توسعه باشد.

اما تعداد Browser هم‌زمان با RAM سرور محدود شود.

Resource Management

سرور موجود:

2 CPU
2GB RAM

است.

بنابراین:

Worker زیاد ایجاد نکن

Browser زیاد اجرا نکن

Concurrency پایین

Queue کنترل‌شده

Memory limits

اجباری.

Docker

Services:

frontend
backend
worker
beat
postgres
redis

در صورت نیاز:

browser

اما تا حد امکان Browser داخل Worker مدیریت شود.

Existing Cofinets Protection

پروژه باید مستقل باشد.

قبل از اجرا:

docker ps
docker network ls
ss -lntup
nginx -T

بررسی شود.

هیچ Port موجود overwrite نشود.

Directory

پیشنهاد:

/opt/apps/cofinets-data-intelligence/

اما ابتدا ساختار فعلی سرور را بررسی کن.

Docker Network

Network اختصاصی:

cofinets_data_network

یا نام منحصر به فرد دیگر.

به Network پروژه‌های دیگر دست نزن.

Ports

سرویس‌ها فقط در صورت نیاز expose شوند.

مثلاً:

Backend → internal
Postgres → internal
Redis → internal
Frontend → internal

Nginx تنها Entry Point عمومی باشد.

Nginx

دامنه:

cofinets.com

چون ممکن است cofinets.com قبلاً سرویس داشته باشد:

قبل از هر تغییر حتماً Configuration فعلی را بخوان.

پروژه جدید را روی Subdomain پیشنهادی اجرا کن:

data.cofinets.com

یا:

scraper.cofinets.com

اما قبل از انتخاب، وضعیت DNS/Nginx موجود را بررسی کن.

اگر امکان Subdomain نیست، از Path یا Domain جدا استفاده کن.

SSL

SSL با Nginx.

قبل از تغییر:

cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup-YYYYMMDD-HHMM

بعد:

nginx -t

و فقط:

systemctl reload nginx

در صورت موفقیت.

Health Endpoint

/health/
/ready/

Health:

Database
Redis
Celery
Storage

API

/api/v1/

Swagger:

/api/docs/

Authentication

امن:

Email
Password
Optional OTP
CAPTCHA
Rate Limit
Password Reset
Session Security

Admin Login

Admin:

2FA

Rate limiting

Secure cookies

Audit

CAPTCHA

CAPTCHA برای:

Login
Password Reset
Sensitive actions

در صورت نیاز.

Cloudflare Turnstile یا سرویس معتبر قابل تنظیم.

Audit Log

ثبت:

Login
Logout
Scraper Create
Scraper Edit
Scraper Run
Export
Data Delete
Data Merge
User Change
Permission Change

Security

اجباری:

DEBUG=False
CSRF
CORS whitelist
XSS protection
SQL Injection protection
Secure cookies
HTTPS
HSTS
Security headers
Rate limiting
File validation
Permission checks

Secrets

هیچ Secret داخل Git.

".env.example":

DJANGO_SECRET_KEY=
DATABASE_URL=
REDIS_URL=
ADMIN_EMAIL=
CAPTCHA_SECRET=
SMTP_PASSWORD=

Export Security

Exportها باید Permission-controlled باشند.

فایل Export نباید URL عمومی قابل حدس داشته باشد.

Download Expiry

در صورت امکان:

Signed URL

یا:

Permission-based download

Personal Data

اطلاعات تماس عمومی سازمان‌ها با:

source
purpose
last_verified

ثبت شود.

برای اطلاعات افراد:

حداقل‌سازی داده

دسترسی Role-based

Audit

Retention

حذف در صورت نیاز

در نظر گرفته شود.

Database Encryption

Secrets را داخل DB ذخیره نکن.

برای داده‌های بسیار حساس در صورت نیاز encryption-at-rest/application-level طراحی شود.

Data Export Policy

سیستم باید مشخص کند چه داده‌ای:

Public
Internal
Restricted
Sensitive

است.

API Permissions

هر Endpoint باید Permission داشته باشد.

Frontend Pages

حداقل:

/login
/dashboard
/sources
/scrapers
/scrapers/{id}
/runs
/data
/data/{id}
/duplicates
/review
/exports
/users
/roles
/settings
/logs
/analytics

Main Dashboard UI

Cards:

Sources
Scrapers
Runs
Records
Errors
Duplicates
Exports

Charts:

Records over time
Scraper success
Records by province
Records by type

Scraper Dashboard

برای هر Scraper:

Status
Last Run
Next Run
Success Rate
Records
Errors
Duration

Scraper Editor UI

Tabs:

General
Source
Method
URLs
Pagination
Fields
Transformations
Validation
Schedule
Limits
Output
Logs
Test

Method Editor

Admin بتواند:

HTTP
Browser
API
Sitemap
RSS
PDF

انتخاب کند.

Field Editor

جدول:

Target Field | Extraction Method | Selector | Transform | Required

Test Panel

دکمه:

Test Extraction

نتیجه:

Raw
Parsed
Normalized
Validation

Run Panel

Run Now
Dry Run
Sample Run
Full Run

Data Explorer UI

قابل استفاده و سریع باشد.

Persian UI

تمام UI فارسی و RTL.

فونت پیشنهادی:

Vazirmatn

یا فونت آزاد و مناسب فارسی دیگر.

Design

Style:

Modern SaaS Dashboard
Professional
Clean
Dark Navy / Blue
Light background
Rounded cards
Subtle shadows

افکت‌ها:

Hover

Fade

Slide

Skeleton

Progress

Toast

بدون افکت‌های سنگین.

Responsive

کاملاً:

Mobile
Tablet
Desktop

Data Table

باید:

Search

Sort

Filter

Pagination

Column toggle

Export

Bulk selection

داشته باشد.

Maps

اگر Map اضافه شد:

Provider configurable.

برای MVP می‌توان از OpenStreetMap در صورت رعایت سیاست استفاده کرد.

Geographic Reports

مثلاً:

استان تهران
داروخانه: 1250
کلینیک: 430
پزشک: 3100

اما اعداد باید از داده واقعی جمع‌آوری‌شده باشند.

Drug Intelligence

در فاز اول:

Drug
Brand
Generic
Manufacturer
Country
Form
Strength
Pack
Source
Demand indicators

Popularity

"Popular" را به‌صورت حدس ثبت نکن.

محاسبه بر اساس داده‌هایی مانند:

Search frequency
Source frequency
Mention frequency
Request data

و همیشه:

Popularity Score
Method
Date

داشته باشد.

Rare Products

"Rare" باید قابل تعریف باشد.

مثلاً:

Low Source Coverage
Low Availability
High Request

نه اینکه سیستم بدون داده ادعا کند محصول کمیاب است.

Seasonal

Seasonal:

Season
Month
Demand Signal
Source

Market Signals

مدل:

MarketSignal

انواع:

DemandIncrease
PriceChange
AvailabilityDrop
NewProduct
SourceMention
SearchIncrease

Data Intelligence

Dashboard:

Trending
Emerging
Declining
Missing
High Demand
Low Supply

با Methodology مشخص.

Source Discovery

سیستم باید بتواند URLهای Seed را دریافت کند.

مثلاً:

Seed URLs

سپس:

Discover Links

ولی Crawl باید فقط در Scope مجاز Source باشد.

Sitemap Discovery

اگر Sitemap وجود داشت:

/sitemap.xml

یا Sitemap Index.

RSS Discovery

RSS Feedها قابل ثبت باشند.

JSON-LD Extraction

اگر صفحه:

application/ld+json

داشت، Parse شود.

برای:

Product
Organization
LocalBusiness
Article

مفید است.

OpenGraph Extraction

استخراج:

og:title
og:description
og:image
og:url

Meta Extraction

title
description
keywords
canonical

Contact Extraction

از صفحات عمومی:

mailto:
tel:
WhatsApp links
Telegram links
Social links

استخراج شود.

فقط اگر واقعاً در صفحه عمومی وجود داشته باشد.

Address Extraction

از:

address
schema.org
Google/Map links if publicly exposed

در صورت مجاز بودن.

Schema.org

Parse:

LocalBusiness
MedicalBusiness
Pharmacy
Physician
MedicalClinic
Organization
Product

هرجا وجود داشته باشد.

Data Normalization

برای:

Name
Phone
Address
City
Province
Brand
Product

Normalization.

Persian Text Processing

Normalize:

Arabic/Persian letters
Whitespace
Half-space
Digits
Punctuation

OCR

Architecture آماده OCR باشد.

در فاز اول اختیاری:

PDF
Image
OCR

اما OCR نباید بدون نیاز فعال باشد.

PDF Extraction

برای PDFهای عمومی:

Text extraction
Metadata
Tables

و در صورت نیاز OCR.

Data Pipeline

Pipeline قابل مشاهده باشد:

RAW
↓
PARSED
↓
NORMALIZED
↓
VALIDATED
↓
DEDUPLICATED
↓
REVIEWED
↓
APPROVED

Record Status

Raw
Parsed
Needs Review
Approved
Rejected
Archived

Import

علاوه بر Scraping:

CSV
XLSX
JSON

Import شود.

Import Wizard

Upload
↓
Detect columns
↓
Map
↓
Preview
↓
Validate
↓
Import

Export

هر View فیلترشده بتواند Export شود.

Background Export

Exportهای بزرگ باید Celery Job باشند.

Notification

وقتی Export آماده شد:

Notification

Project System

Admin بتواند Project بسازد:

Healthcare
Drug
Pharmacy
Clinic
Industrial
Automotive

هر Project:

Sources
Scrapers
Entities
Users
Exports

داشته باشد.

Multi-Tenant Ready

فعلاً Single Organization.

اما Architecture طوری باشد که آینده Multi-Tenant ممکن باشد.

API-first

تمام عملیات اصلی Backend API داشته باشند.

Documentation

بساز:

README.md
docs/ARCHITECTURE.md
docs/DEPLOYMENT.md
docs/SCRAPERS.md
docs/PARSERS.md
docs/DATA_MODEL.md
docs/SECURITY.md
docs/API.md
docs/EXPORTS.md
docs/TROUBLESHOOTING.md
docs/OPERATIONS.md

Troubleshooting

برای خطاهای رایج:

Database unavailable
Redis unavailable
Celery not running
Playwright unavailable
Nginx error
SSL error
Port collision
Migration error
Permission error
Memory error

راهکار دقیق بده.

Health Check Script

بساز:

scripts/healthcheck.sh

Backup

بساز:

scripts/backup.sh
scripts/restore.sh

Backup:

PostgreSQL
Media
Configuration
Scraper definitions

Backup Safety

Backup نباید داخل Git باشد.

Server Deployment

Deployment باید مرحله‌ای باشد.

ابتدا:

uname -a
cat /etc/os-release
docker --version
docker compose version
df -h
free -h
ss -lntup
docker ps
nginx -T

Existing Cofinets

هیچ چیزی را حذف نکن.

هیچ:

docker compose down

روی پروژه‌های دیگر اجرا نکن.

Directory Creation

بعد از بررسی:

mkdir -p /opt/apps/cofinets-data-intelligence

یا مسیر مناسب.

Docker Compose

از Network و Volume اختصاصی استفاده کن.

Resource Limits

به دلیل 2GB RAM:

مثلاً Worker:

1-2

و Browser concurrency:

1

به‌صورت پیش‌فرض.

قابل تنظیم.

Production Build

Frontend production build.

Backend Gunicorn.

Nginx

Nginx:

HTTPS
Compression
Static
Media
Proxy
Security headers

Domain

قبل از اتصال Domain:

DNS بررسی شود.

پیشنهاد:

data.cofinets.com

ولی اگر این Subdomain مناسب نبود، Agent باید وضعیت فعلی "cofinets.com" را بررسی کند و بدون تخریب سرویس موجود گزینه مناسب را انتخاب/پیشنهاد کند.

SSL

Let's Encrypt یا Certificate موجود.

Nginx Validation

قبل از Reload:

nginx -t

فقط در صورت:

syntax is ok
test is successful

سپس:

systemctl reload nginx

Final URL

در پایان باید:

https://data.cofinets.com

یا Domain نهایی تعیین‌شده قابل استفاده باشد.

Git

ساختار:

.gitignore
README.md
CHANGELOG.md
LICENSE

No Secrets

".env" داخل ZIP نباشد.

".env.example" باشد.

Tests

Backend:

Unit
Integration
API
Parser
Normalizer
Deduplication
Export
Permission

Scraper Tests

برای هر Parser حداقل Fixture داشته باش.

مثلاً:

tests/fixtures/pharmacy/
tests/fixtures/drug/
tests/fixtures/clinic/

تا اگر Source تغییر کرد بتوان Parser را تست کرد.

Fixture

HTML واقعی را فقط در صورتی نگه دار که استفاده از آن مجاز باشد؛ در غیر این صورت Fixture مصنوعی/نمونه بساز.

Parser Regression

اگر Parser خراب شد:

Regression Test

باید Fail شود.

CI

در صورت امکان:

GitHub Actions

برای:

Lint
Tests
Build

Code Quality

Python:

ruff
pytest
mypy

در صورت سازگاری.

Frontend:

eslint
prettier
typescript

Logging

Structured logging.

Metrics

در صورت امکان:

Scrape duration
Records/minute
Error rate
Success rate
Queue length

Observability

در فاز بعد:

Prometheus
Grafana
Sentry

قابل اضافه شدن باشد.

برای سرور 2GB فعلاً همه را فعال نکن مگر واقعاً ضروری باشد.

Admin Settings

Settings:

General
Scraping
Rate Limits
Storage
Exports
Notifications
Security
Retention

Global Configuration

مقادیر مهم از UI قابل تنظیم باشند ولی Secretها فقط ".env".

Dynamic Scraper Configuration

Admin بتواند:

Enable
Disable
Clone
Edit
Test
Run
Schedule
Archive

Clone Scraper

مثلاً:

Pharmacy Tehran

Clone شود:

Pharmacy Tabriz

و فقط URL/Filter تغییر کند.

Template Scrapers

چند Template:

Directory Scraper
Product Scraper
Article Scraper
Pharmacy Scraper
Clinic Scraper
Doctor Scraper
Company Scraper

Generic Scraper Wizard

Wizard:

Source

Entity

URL

Method

Fields

Test

Schedule

Save

Data Preview

قبل از Run:

Preview 10 records

Export Preview

قبل از Export:

Records: 12,340
Columns: 18
Filters: Tehran

Export Permissions

فقط Role مجاز بتواند Export حساس انجام دهد.

Download History

ثبت:

User
Export
Time
Filters

Audit

هیچ Bulk Delete بدون Confirmation دومرحله‌ای انجام نشود.

Recovery

Soft Delete و Backup برای داده‌های مهم.

Admin UX

Admin باید:

سریع

ساده

فارسی

قابل جستجو

قابل فیلتر

حرفه‌ای

باشد.

UI Components

Reusable:

Sidebar
Topbar
Breadcrumb
StatsCard
DataTable
FilterBar
SearchBox
Modal
Drawer
Tabs
Toast
ConfirmDialog
CodeEditor
SelectorTester
ProgressBar
Timeline
LogViewer

Scraper UI Code Editor

برای Selector/Ruleها:

Syntax highlighting مناسب.

اما اجرای arbitrary code ممنوع.

Dark Mode

اختیاری ولی architecture آماده.

Accessibility

حداقل:

Keyboard
Contrast
Focus
Labels
ARIA

Performance

Frontend:

Code splitting
Lazy loading
Image optimization
Pagination
Virtualization where needed

Backend:

select_related
prefetch_related
indexes
pagination
caching

Cache

Redis:

Dashboard
Source status
Search
Metadata

Search

MVP:

PostgreSQL Full Text Search.

Architecture آماده برای:

OpenSearch

Search Fields

Name
Brand
Phone
Address
City
Province
Product
Specialty

Fuzzy Search

در صورت امکان:

PostgreSQL trigram

Persian Search

Normalize:

ی/ي
ک/ك

قبل از Search.

Data Quality Dashboard

مثلاً:

Complete
Incomplete
Needs Review
Duplicate
Stale

Stale Data

هر Record:

last_verified

داشته باشد.

اگر قدیمی شد:

Stale

Verification

Admin بتواند:

Verify
Reject
Request Review

Source Citation

هر Record:

Source URL
Source Name
Collected At

را نشان دهد.

Manual Verification

در UI:

Open Source
Compare
Verify

Data Lineage

از Record نهایی بتوان فهمید:

Source
Scraper
Parser
Run
Transformation

Export Lineage

Export نیز باید Filter و Source را ذخیره کند.

API Data Access

در آینده API Key برای User/Customer قابل اضافه شدن باشد.

API Key

Architecture:

ApiKey
ApiUsage
ApiPermission

API Rate Limit

برای هر API Key.

Data Licensing

هر Source:

Usage Policy

داشته باشد.

Compliance

در Source:

Allowed for Storage
Allowed for Internal Use
Allowed for Export
Allowed for Commercial Use

به‌صورت Metadata نگهداری شود.

اگر وضعیت نامشخص است، Export عمومی آن Source مجاز فرض نشود.

Commercial Data

اگر داده‌ای برای استفاده تجاری مجاز نیست:

سیستم باید امکان:

Internal Only

داشته باشد.

PII Protection

اطلاعات شخصی حساس:

Restricted

و در Export عمومی حذف یا Mask شوند.

Masking

مثلاً:

0912******12

برای Roleهای محدود.

Data Sales Future

اگر در آینده فروش Data فعال شد، سیستم باید قبل از Export:

License
Consent
Source Rights
Data Classification

را بررسی کند.

No Automatic Public Publishing

داده خام Scraper نباید مستقیم Public شود.

Pipeline:

Scraped
→ Review
→ Approved
→ Published

Project Separation

داده Healthcare از سایر صنایع جدا باشد.

Taxonomy

Category system:

Healthcare
├── Drugs
├── Pharmacies
├── Clinics
├── Doctors
└── Medical Equipment

بعداً:

Industrial
Automotive
Electrical

اضافه شود.

Data Tags

مثلاً:

Rare
Popular
Seasonal
Verified
High Quality
Needs Review

Bulk Tagging

Admin بتواند چند Record را Tag کند.

Reports

گزارش‌های آماده:

Pharmacies by Province
Clinics by City
Doctors by Specialty
Drugs by Brand
Records by Source
Records by Date
Data Quality
Scraper Performance

Report Builder

Architecture آماده Report Builder.

Export Naming

مثلاً:

pharmacies-tehran-2026-09-18.xlsx

Persian Filenames

در صورت امکان نام فایل فارسی هم قابل انتخاب باشد، ولی Filename امن و UTF-8 باشد.

ZIP

در پایان:

cofinets-data-intelligence-v1.0.0.zip

ساخته شود.

ZIP Content

cofinets-data-intelligence/
├── backend/
├── frontend/
├── deploy/
├── docs/
├── scripts/
├── tests/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── README.md
├── CHANGELOG.md
└── LICENSE

ZIP Security

داخل ZIP:

NO .env
NO secrets
NO passwords
NO private keys
NO production database
NO tokens

ZIP Validation

اجرا:

unzip -t cofinets-data-intelligence-v1.0.0.zip

و سپس:

sha256sum cofinets-data-intelligence-v1.0.0.zip

Checksum را گزارش کن.

Installation Guide

یک دستورالعمل کامل فارسی بنویس.

مثلاً:

SSH
↓
Backup
↓
Upload
↓
Extract
↓
Configure ENV
↓
Build
↓
Migrate
↓
Create Admin
↓
Start
↓
Health Check
↓
Nginx
↓
SSL
↓
DNS

Exact Server Commands

دستورات باید واقعی و قابل Copy/Paste باشند.

قبل از هر دستور خطرناک توضیح بده چه می‌کند.

Backup Before Deployment

قبل از Deployment:

docker ps
nginx -T > nginx-before.txt

و Backup مناسب.

Nginx Backup

مثلاً:

cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup-$(date +%Y%m%d-%H%M%S)

و Configuration سایت موجود نیز backup شود.

Nginx Change

Configuration جدید را:

/etc/nginx/sites-available/

قرار بده.

Symlink جدا.

هرگز فایل موجود را overwrite نکن.

Nginx Test

nginx -t

اگر fail شد:

Reload نکن.

Deployment Verification

docker compose ps
docker compose logs --tail=100
curl -I https://data.cofinets.com
curl https://data.cofinets.com/health/

Rollback

اگر Health Check fail شد:

Stop new service
Restore previous configuration
Restore DB if necessary
Reload Nginx

اما Database rollback فقط طبق migration/backup strategy.

Final QA

حتماً:

[ ] Login
[ ] Admin
[ ] RBAC
[ ] Source
[ ] Scraper
[ ] Parser
[ ] Test extraction
[ ] Dry run
[ ] Full run
[ ] Data Explorer
[ ] Dedup
[ ] Review
[ ] Export CSV
[ ] Export XLSX
[ ] Export DOCX
[ ] Export JSON
[ ] Scheduler
[ ] Logs
[ ] Error handling
[ ] Backup
[ ] Restore
[ ] HTTPS
[ ] Nginx
[ ] Existing Cofinets untouched

Development Workflow

هر Phase:

Implement
→ Test
→ Review
→ Fix
→ Document

Do Not Hide Errors

اگر چیزی کار نمی‌کند:

نگو:

Done

بلکه دقیقاً بگو:

Failed
Reason
Affected files
Logs
Fix

No Fake Completion

اگر ZIP ساخته نشده:

نگو ساخته شد.

اگر Deployment انجام نشده:

نگو انجام شد.

اگر تست نشده:

نگو تست شد.

Final Deliverable

در پایان:

PROJECT
↓
SOURCE CODE
↓
BUILD
↓
TEST
↓
ZIP
↓
DEPLOYMENT GUIDE

را ارائه کن.

Final Response Format

در پایان پاسخ:

=====================================
COFINETS DATA INTELLIGENCE

Version:
Status:

Backend:
Frontend:
Database:
Scraper Engine:
Parser Engine:
Scheduler:
Exports:
Authentication:
RBAC:
Security:
Tests:
Docker:
Nginx:
Domain:
Backup:
ZIP:

Records Tested:
Scrapers Tested:
Exports Tested:

Known Issues:

Files:

Deployment Commands:

Health Check:

Rollback:

Next Recommended Improvements:

اولویت‌بندی پیاده‌سازی

اگر زمان یا منابع محدود بود، اولویت:

P0
Authentication
RBAC
Database
Source Management
Scraper Engine
Parser
Data Explorer
Export
Admin

P1
Scheduler
Deduplication
Quality
Review
Geography
Analytics

P2
Browser scraping
PDF
OCR
Advanced intelligence
Maps
API

P3
OpenSearch
Advanced analytics
Multi-tenant
Commercial Data API

قانون نهایی

این پروژه را به‌عنوان یک محصول واقعی SaaS داخلی تصور کن.

نه Script.

نه Demo.

نه Prototype.

باید:

سریع باشد

ساده باشد

فارسی باشد

RTL باشد

زیبا باشد

امن باشد

قابل توسعه باشد

قابل Debug باشد

قابل Backup باشد

قابل Restore باشد

قابل Dockerize باشد

قابل Deployment باشد

قابل توسعه برای صنایع دیگر باشد.

تمرکز نسخه اول:

جمع‌آوری و مدیریت داده‌های عمومی حوزه دارو، داروخانه، پزشک، مطب و کلینیک

اما Core سیستم باید Generic باشد.

چرخه اصلی:

SOURCE
↓
DISCOVERY
↓
FETCH
↓
PARSE
↓
EXTRACT
↓
NORMALIZE
↓
VALIDATE
↓
DEDUPLICATE
↓
QUALITY SCORE
↓
REVIEW
↓
APPROVE
↓
STORE
↓
ANALYZE
↓
EXPORT

این چرخه باید ستون فقرات کل پروژه باشد.

شروع پروژه را از بررسی محیط فعلی سرور و معماری موجود Cofinets آغاز کن و هیچ تغییری روی سرویس‌های موجود بدون بررسی و Backup انجام نده.

