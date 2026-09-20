# CDI real-market benchmark — Gardasil 9 / Iran

## Purpose

This benchmark validates CDI against a real public Iranian medicine-information page before the crawler is promoted to a broader market crawl.

Target observed during project development:

- Source: Pillix
- URL: https://pillix.ir/medicine/med-mivz
- Product: Gardasil 9 / 9-valent human papillomavirus vaccine
- Expected entity family: medicine / vaccine
- Expected geography: Iran

The page currently exposes product name, English name, generic name, manufacturer/brand information and ATC classification. The source itself states that its drug information is received from the country's drug-information system and also identifies pharmacy/city navigation. This makes it useful as a market-data smoke source, but the source remains third-party and every extracted field must retain provenance.

## What CDI must prove

1. The public URL is fetched through the bounded fetcher.
2. robots/domain/redirect controls remain active.
3. Raw HTML is captured with SHA-256 provenance.
4. At least one structured record is extracted.
5. Persian text survives extraction and normalization.
6. The source URL/domain are stored on the record.
7. A deterministic fingerprint is produced.
8. A second run does not create a duplicate record when the fingerprint is unchanged.
9. The result can be exported as CSV/XLSX/JSON/JSONL/TXT/DOCX/PDF.
10. The crawler does not claim pharmacy stock merely because a medicine page exists.

## Server command

Run only on the isolated CDI stack:

    docker compose exec backend python manage.py cdi_market_smoke

For an actual persisted market run:

    docker compose exec backend python manage.py cdi_market_smoke --persist

The default target is intentionally one page. Increase scope only after this single-page benchmark passes.

## Acceptance criteria

A valid first run should report:

- capture status: success
- records: at least 1
- source domain: pillix.ir
- non-empty Persian product field
- non-empty source URL
- non-empty fingerprint

If the source blocks the request, robots policy changes, or the HTML structure changes, the command must fail loudly rather than silently producing empty data.

## Market interpretation

A product page is evidence that the source publishes information about that product. It is NOT evidence that a particular Iranian pharmacy currently has stock.

Stock, price and pharmacy-level availability require a separate source/entity model with timestamped observations. This distinction is mandatory for the production data model.
