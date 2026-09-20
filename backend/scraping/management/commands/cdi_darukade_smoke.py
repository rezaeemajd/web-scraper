import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from datahub.models import EntityField, EntityType
from datahub.pipeline import process_records
from scraping.adapters.darukade_product import extract_products
from scraping.models import Scraper
from sources.fetcher import capture_url
from sources.models import Source


DEFAULT_URL = "https://darukade.com/products"


class DryRunRollback(Exception):
    pass


class Command(BaseCommand):
    help = "Run a bounded real-world Darukade retail product smoke through CDI."

    def add_arguments(self, parser):
        parser.add_argument("--url", default=DEFAULT_URL)
        parser.add_argument("--persist", action="store_true")

    def handle(self, *args, **options):
        url = options["url"]
        persist = options["persist"]

        def run_once():
            source, _ = Source.objects.get_or_create(
                domain="darukade.com",
                defaults={
                    "name": "Darukade",
                    "base_url": "https://darukade.com",
                    "respect_robots": True,
                    "rate_limit_per_minute": 10,
                    "max_response_bytes": 5 * 1024 * 1024,
                },
            )
            entity, _ = EntityType.objects.get_or_create(
                slug="darukade-retail-product",
                defaults={
                    "name": "محصول داروخانه‌ای / خرده‌فروشی — داروکده",
                    "description": "Retail product observations from Darukade.",
                },
            )
            fields = {
                "name": ("نام محصول", True),
                "brand": ("برند", False),
                "price_text": ("قیمت مشاهده‌شده", False),
                "detail_url": ("صفحه محصول", False),
                "observation_type": ("نوع مشاهده", False),
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
                name="Darukade — retail products",
                source=source,
                defaults={
                    "start_url": url,
                    "entity_type": entity,
                    "parser_version": "1.0.0",
                    "extraction_config": {"adapter": "darukade", "max_records": 100},
                },
            )
            scraper.start_url = url
            scraper.entity_type = entity
            scraper.parser_version = "1.0.0"
            scraper.extraction_config = {"adapter": "darukade", "max_records": 100}
            scraper.active = True
            scraper.save()

            capture = capture_url(source, url)
            if capture.status != capture.Status.SUCCESS:
                return source, capture, []

            items = extract_products(capture.body, url)[:100]
            records = process_records(
                entity_type=entity,
                items=[
                    {
                        "url": item["source_url"],
                        "payload": item,
                        "raw_capture": capture,
                        "evidence": [
                            {
                                "field": "name",
                                "selector": "a[href^='/products/']",
                                "value": item["name"],
                            },
                            {
                                "field": "price_text",
                                "selector": "product-listing-card",
                                "value": item["price_text"],
                            },
                        ],
                        "source_domain": source.domain,
                    }
                    for item in items
                ],
                fields=list(entity.fields.all()),
                batch_size=100,
            )
            return source, capture, records

        if persist:
            source, capture, records = run_once()
            rolled_back = False
        else:
            holder = {}
            try:
                with transaction.atomic():
                    holder["value"] = run_once()
                    raise DryRunRollback
            except DryRunRollback:
                pass
            source, capture, records = holder["value"]
            rolled_back = True

        result = {
            "source": source.domain,
            "url": url,
            "capture_status": capture.status,
            "status_code": capture.status_code,
            "records": len(records),
            "persisted": persist,
            "rolled_back": rolled_back,
            "sample": [
                {
                    "source_url": record.source_url,
                    "payload": record.payload,
                    "fingerprint": record.fingerprint,
                }
                for record in records[:5]
            ],
        }
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))

        if capture.status != capture.Status.SUCCESS:
            raise CommandError(capture.error_message or "Darukade source was not fetched")
        if not records:
            raise CommandError("Darukade parser extracted zero retail product records")
