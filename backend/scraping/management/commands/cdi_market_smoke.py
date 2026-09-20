import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from datahub.models import EntityField, EntityType
from scraping.engine import execute_many
from scraping.models import Scraper
from sources.models import Source


DEFAULT_URL = "https://pillix.ir/medicine/med-mivz"
DEFAULT_DOMAIN = "pillix.ir"
DRY_RUN_SENTINEL = object()


class Command(BaseCommand):
    help = "Run a bounded real-world Iranian medicine-market benchmark."

    def add_arguments(self, parser):
        parser.add_argument("--url", default=DEFAULT_URL)
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
                "product_name": ("نام فرآورده", True),
                "english_name": ("نام انگلیسی", False),
                "brand_line": ("برند / محصول", False),
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
                "fields": {
                    "product_name": "h1:nth-of-type(1)",
                    "english_name": "h1:nth-of-type(2)",
                    "brand_line": "h1:nth-of-type(3)",
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

            result = execute_many(
                scraper,
                collect_records=True,
                collect_captures=True,
            )
            if len(result) == 2:
                records, captures = result
                count = len(records)
            else:
                records, captures, count = result
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

        if not captures:
            raise CommandError("no HTTP capture was produced")
        first = captures[0]
        if first.status != first.Status.SUCCESS:
            raise CommandError(first.error_message or "market source was not fetched")
        if count < 1:
            raise CommandError("market benchmark extracted zero records")
        if not records:
            raise CommandError("benchmark produced no in-memory records")
