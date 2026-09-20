import json

from django.core.management.base import BaseCommand, CommandError

from datahub.models import EntityField, EntityType
from scraping.engine import execute_many
from scraping.models import Scraper
from sources.models import Source


DEFAULT_URL = "https://pillix.ir/medicine/med-mivz"
DEFAULT_DOMAIN = "pillix.ir"


class Command(BaseCommand):
    help = "Run a real-world Iranian market smoke test against a configured public medicine page."

    def add_arguments(self, parser):
        parser.add_argument("--url", default=DEFAULT_URL)
        parser.add_argument("--domain", default=DEFAULT_DOMAIN)
        parser.add_argument("--max-pages", type=int, default=1)
        parser.add_argument("--persist", action="store_true")

    def handle(self, *args, **options):
        url = options["url"]
        domain = options["domain"]
        max_pages = options["max_pages"]
        if not 1 <= max_pages <= 10:
            raise CommandError("--max-pages must be between 1 and 10")

        source, _ = Source.objects.get_or_create(
            domain=domain,
            defaults={
                "name": "Iran medicine market smoke source",
                "base_url": f"https://{domain}",
                "respect_robots": True,
                "rate_limit_per_minute": 10,
                "max_response_bytes": 5 * 1024 * 1024,
            },
        )

        entity, _ = EntityType.objects.get_or_create(
            slug="market-medicine",
            defaults={
                "name": "دارو / واکسن بازار ایران",
                "description": "Real-world market smoke-test entity.",
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

        scraper, _ = Scraper.objects.get_or_create(
            name="Iran market — Gardasil 9 smoke test",
            source=source,
            defaults={
                "start_url": url,
                "entity_type": entity,
                "parser_version": "1.0.0",
                "extraction_config": {
                    "record_selector": "body",
                    "fields": {
                        "product_name": "h1:nth-of-type(1)",
                        "english_name": "h1:nth-of-type(2)",
                        "brand_line": "h1:nth-of-type(3)",
                    },
                    "pagination": {"max_pages": max_pages},
                },
            },
        )

        scraper.start_url = url
        scraper.entity_type = entity
        scraper.extraction_config = {
            "record_selector": "body",
            "fields": {
                "product_name": "h1:nth-of-type(1)",
                "english_name": "h1:nth-of-type(2)",
                "brand_line": "h1:nth-of-type(3)",
            },
            "pagination": {"max_pages": max_pages},
        }
        scraper.active = True
        scraper.save(update_fields=["start_url", "entity_type", "extraction_config", "active"])

        records, captures, count = execute_many(
            scraper,
            collect_records=options["persist"],
            collect_captures=True,
        )

        result = {
            "source": domain,
            "url": url,
            "captures": len(captures),
            "records": count,
            "capture_statuses": [capture.status for capture in captures],
            "persisted": options["persist"],
            "sample": [
                {
                    "source_url": record.source_url,
                    "payload": record.payload,
                    "fingerprint": record.fingerprint,
                }
                for record in records[:3]
            ],
        }
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))

        if not captures:
            raise CommandError("no HTTP capture was produced")
        if captures[0].status != captures[0].Status.SUCCESS:
            raise CommandError(captures[0].error_message or "market source was not fetched")
        if count < 1:
            raise CommandError("market smoke test extracted zero records")
