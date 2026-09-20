import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from datahub.models import EntityField, EntityType
from scraping.engine import execute_many
from scraping.models import Scraper
from sources.models import Source


DEFAULT_URL = "https://pillix.ir/medicine/med-mivz"
DEFAULT_VARIANT_URL = "https://pillix.ir/medicine/med-bhl4"
DEFAULT_DOMAIN = "pillix.ir"
DRY_RUN_SENTINEL = object()


class Command(BaseCommand):
    help = "Run a bounded real-world Iranian medicine-market benchmark."

    def add_arguments(self, parser):
        parser.add_argument("--url", default=DEFAULT_URL)
        parser.add_argument("--variant-url", default=DEFAULT_VARIANT_URL,
                            help="Second real Gardasil 9 variant used for identity/dedup comparison.")
        parser.add_argument("--domain", default=DEFAULT_DOMAIN)
        parser.add_argument("--max-pages", type=int, default=1)
        parser.add_argument(
            "--persist",
            action="store_true",
            help="Commit the source, capture, scraper, records and observations. "
            "Without this flag the entire benchmark transaction is rolled back.",
        )

    def handle(self, *args, **options):
        url = options["url"]
        variant_url = options["variant_url"]
        domain = options["domain"]
        max_pages = options["max_pages"]
        persist = options["persist"]
        if not 1 <= max_pages <= 10:
            raise CommandError("--max-pages must be between 1 and 10")

        def run_once():
            source, _ = Source.objects.get_or_create(
                domain=domain,
                defaults={
                    "name": "Iran medicine market benchmark source",
                    "base_url": f"https://{domain}",
                    "respect_robots": True,
                    "rate_limit_per_minute": 10,
                    "max_response_bytes": 5 * 1024 * 1024,
                },
            )
            source.base_url = f"https://{domain}"
            source.respect_robots = True
            source.rate_limit_per_minute = max(1, source.rate_limit_per_minute or 10)
            source.max_response_bytes = min(
                max(64 * 1024, source.max_response_bytes or 5 * 1024 * 1024),
                5 * 1024 * 1024,
            )
            source.save(
                update_fields=[
                    "base_url",
                    "respect_robots",
                    "rate_limit_per_minute",
                    "max_response_bytes",
                ]
            )

            entity, _ = EntityType.objects.get_or_create(
                slug="market-medicine",
                defaults={
                    "name": "دارو / واکسن بازار ایران",
                    "description": "Bounded real-world medicine/vaccine market benchmark entity.",
                },
            )

            fields = {
                "product_name": ("نام", True),
                "english_name": ("نام انگلیسی", False),
                "generic_name": ("نام دارو", False),
                "generic_name_full": ("نام عمومی دارو", False),
                "generic_name_english": ("نام عمومی دارو به انگلیسی", False),
                "dosage_form": ("شکل دارویی", False),
                "route": ("نحوه مصرف", False),
                "strength": ("قدرت", False),
                "amount": ("میزان", False),
                "molecule": ("مولکول", False),
                "license_holder": ("صاحب پروانه", False),
                "brand_owner": ("صاحب برند", False),
                "manufacturer": ("تولیدکننده", False),
                "manufacturing_country": ("کشور تولیدکننده", False),
                "license_valid_until": ("تاریخ اعتبار پروانه", False),
                "consumer_price": ("قیمت مصرف کننده هر بسته", False),
                "unit_price": ("قیمت واحد", False),
                "package": ("تعداد در بسته", False),
                "atc_code": ("کد ATC", False),
            }
            for slug, (name, identifier) in fields.items():
                EntityField.objects.get_or_create(
                    entity_type=entity,
                    slug=slug,
                    defaults={
                        "name": name,
                        "is_identifier": identifier,
                        "is_blocking": identifier,
                        "searchable": True,
                    },
                )

            extraction_config = {
                "fields": {},
                "label_table": {
                    "product_name": ["نام"],
                    "english_name": ["نام به انگلیسی"],
                    "generic_name": ["نام دارو"],
                    "generic_name_full": ["نام عمومی دارو"],
                    "generic_name_english": ["نام عمومی دارو به انگلیسی"],
                    "dosage_form": ["شکل دارویی"],
                    "route": ["نحوه مصرف"],
                    "strength": ["قدرت"],
                    "amount": ["میزان"],
                    "molecule": ["مولکول"],
                    "license_holder": ["صاحب پروانه"],
                    "brand_owner": ["صاحب برند"],
                    "manufacturer": ["تولیدکننده"],
                    "manufacturing_country": ["کشور تولیدکننده"],
                    "license_valid_until": ["تاریخ اعتبار پروانه"],
                    "consumer_price": ["قیمت مصرف کننده هر بسته"],
                    "unit_price": ["قیمت واحد"],
                    "package": ["تعداد در بسته"],
                },
                "regex_fields": {
                    "atc_code": {"selector": "body", "pattern": "\\bJ07BM\\d{2}\\b"},
                },
                "pagination": {"max_pages": max_pages},
            }

            scraper, _ = Scraper.objects.get_or_create(
                name="Iran market — Gardasil 9 benchmark",
                source=source,
                defaults={
                    "start_url": url,
                    "entity_type": entity,
                    "parser_version": "1.1.0",
                    "extraction_config": extraction_config,
                },
            )
            scraper.start_url = url
            scraper.entity_type = entity
            scraper.parser_version = "1.1.0"
            scraper.extraction_config = extraction_config
            scraper.active = True
            scraper.save(
                update_fields=[
                    "start_url",
                    "entity_type",
                    "parser_version",
                    "extraction_config",
                    "active",
                ]
            )

            records = []
            captures = []
            count = 0
            for target_url in [url, variant_url]:
                scraper.start_url = target_url
                scraper.save(update_fields=["start_url"])
                result = execute_many(
                    scraper,
                    collect_records=True,
                    collect_captures=True,
                )
                if len(result) == 2:
                    page_records, page_captures = result
                    page_count = len(page_records)
                else:
                    page_records, page_captures, page_count = result
                records.extend(page_records)
                captures.extend(page_captures)
                count += page_count
            return source, scraper, records, captures, count

        if persist:
            _, scraper, records, captures, count = run_once()
            rolled_back = False
        else:
            holder = {}

            class DryRunRollback(Exception):
                pass

            try:
                with transaction.atomic():
                    holder["value"] = run_once()
                    raise DryRunRollback
            except DryRunRollback:
                pass
            _, scraper, records, captures, count = holder["value"]
            rolled_back = True

        result = {
            "source": domain,
            "url": url,
            "variant_url": variant_url,
            "captures": len(captures),
            "records": count,
            "capture_statuses": [capture.status for capture in captures],
            "persisted": persist,
            "rolled_back": rolled_back,
            "sample": [
                {
                    "source_url": record.source_url,
                    "payload": record.payload,
                    "normalized_payload": record.normalized_payload,
                    "fingerprint": record.fingerprint,
                }
                for record in records[:3]
            ],
        }
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))

        if len(captures) < 2:
            raise CommandError("both real Gardasil variant pages must produce captures")
        if not captures:
            raise CommandError("no HTTP capture was produced")
        first = captures[0]
        if first.status != first.Status.SUCCESS:
            raise CommandError(first.error_message or "market source was not fetched")
        if count < 1:
            raise CommandError("market benchmark extracted zero records")
        if not records:
            raise CommandError("benchmark produced no in-memory records")
