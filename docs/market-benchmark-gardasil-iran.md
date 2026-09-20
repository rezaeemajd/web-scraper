# CDI real-market benchmark — Gardasil 9 / Iran

## Purpose

This benchmark is the first real-market acceptance path for CDI. It validates the complete bounded pipeline against a live Iranian medicine-information page before the crawler is expanded to pharmacy, city and province observations.

Current live source evidence confirms that the target page publishes:

- Persian product name
- English name / brand
- generic medicine name
- dosage/form information
- manufacturer and brand-owner information
- country of manufacture
- licence validity date
- consumer/unit price fields
- ATC classification
- a pharmacy-search entry point

The page identifies itself as receiving medicine information from the country's medicine-information system, while also stating that the website is not responsible for the correctness of that information. CDI therefore stores the page as third-party source evidence and never promotes it to regulatory truth or pharmacy stock truth.

## Target

- Source: Pillix
- Domain: pillix.ir
- URL: https://pillix.ir/medicine/med-mivz
- Product family: Gardasil 9 / 9-valent HPV vaccine
- Expected entity family: medicine / vaccine
- Expected geography: Iran

The same source currently exposes more than one Gardasil-related product page. This is useful for later identity/dedup benchmarking, but the first acceptance run intentionally remains one page.

## What CDI must prove

1. Public URL is fetched through the bounded fetcher.
2. robots/domain/redirect/private-network controls remain active.
3. Raw HTML is captured with SHA-256 provenance.
4. At least one structured record is extracted.
5. Persian text survives normalization.
6. Source URL/domain remain attached to the record.
7. A deterministic fingerprint is produced.
8. A second persisted run is idempotent when the normalized identity/fingerprint is unchanged.
9. Observation history can record a later change without overwriting the previous observation.
10. Export can serialize the record in CSV/XLSX/JSON/JSONL/TXT/DOCX/PDF.
11. The crawler does not claim pharmacy stock merely because a medicine page exists.

## Server commands

Run only on the isolated CDI stack.

Dry-run benchmark (fetch/parse/pipeline execution is rolled back at the DB transaction boundary):

    docker compose exec backend python manage.py cdi_market_smoke

Persisted benchmark:

    docker compose exec backend python manage.py cdi_market_smoke --persist

The default scope is exactly one page. Do not increase the scope until the one-page acceptance criteria pass.

## Expected acceptance output

A successful run should contain:

- capture status: success
- records: at least 1
- source domain: pillix.ir
- non-empty Persian product field
- non-empty English/brand field
- non-empty source URL
- non-empty fingerprint
- normalized Persian characters (for example ی/ک normalization)
- evidence entries identifying the CSS selectors used

If the source blocks the request, robots policy changes, DNS resolves to a non-public address, an external redirect is attempted, or the HTML structure no longer exposes the expected fields, the benchmark must fail loudly.

## Why the dry-run is safe

The non-persisted command executes the same real fetch and extraction path but wraps source/scraper/capture/record/observation writes in an outer database transaction and deliberately rolls that transaction back after collecting the result. The cache-based request limiter is intentionally outside the DB transaction and may consume one rate-limit slot; it does not create market data.

This avoids the previous failure mode where a command labelled "smoke" could still leave database records behind.

## Market interpretation

A product page is evidence that the source publishes information about that product. It is **not** evidence that a particular Iranian pharmacy currently has stock.

These are separate CDI facts:

    Drug information
        != Pharmacy availability
        != Current stock
        != Legal/import status
        != Market price

Pharmacy availability and price must be modelled as timestamped observations tied to a specific pharmacy/location/source. A historical or commercial claim must never be silently promoted to a current national market fact.

## Next benchmark expansion

After the single Gardasil page passes:

1. Compare the two currently discoverable Gardasil 9 product variants from the same source.
2. Add source-specific structured field extraction for manufacturer, licence, ATC and package data.
3. Add a dedicated Pharmacy entity and pharmacy-location observation model.
4. Crawl a bounded set of Gardasil pharmacy result pages, preserving source URL and observation timestamp.
5. Validate city/province extraction.
6. Expose the resulting data through the explorer API.
7. Only then expand to a small real-market staging crawl.

The expansion must remain bounded, provenance-first and reversible.
