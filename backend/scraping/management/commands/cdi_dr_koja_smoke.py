import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from datahub.models import EntityField, EntityType
from datahub.pipeline import process_records
from scraping.adapters.dr_koja_drug import extract_drugs
from scraping.models import Scraper
from sources.fetcher import capture_url
from sources.models import Source


DEFAULT_URL = "https://dr-koja.ir/drugs"
DRY_RUN_SENTINEL = object()


class DryRunRollback(Exception):
    pass


class Command(BaseCommand):
    help = "Run a bounded real-world Dr-Koja drug-index smoke through CDI."

    def add_arguments(self, parser):
        parser.add_argument("--url", default=DEFAULT_URL)
        parser.add_argument("--persist", action="store_true")

    def handle(self, *args, **options):
        url = options["url"]
        persist = options["persist"]

        def run_once():
            source, _ = Source.objects.get_or_create(
                domain="dr-koja.ir",
                defaults={
                    "name": "Dr-Koja",
                    "base_url": "https://dr-koja.ir",
                    "respect_robots": True,
                    "rate_limit_per_minute": 10,
                    "max_response_bytes": 5 * 1024 * 1024,
                },
            )
            source.name = "Dr-Koja"
            source.base_url = "https://dr-koja.ir"
            source.respect_robots = True
            source.rate_limit_per_minute = max(1, source.rate_limit_per_minute or 10)
            source.max_response_bytes = min(
                max(64 * 1024, source.max_response_bytes or 5 * 1024 * 1024),
                5 * 1024 * 1024,
            )
            source.save(update_fields=[
                "name", "base_url", "respect_robots",
                "rate_limit_per_minute", "max_response_bytes",
            ])

            entity, _ = EntityType.objects.get_or_create(
                slug="dr-koja-drug",
                defaults={
                    "name": "دارو — Dr-Koja",
                    "description": "Public drug index records captured from Dr-Koja with source provenance.",
                },
            )
            fields = {
                "name": ("نام دارو", True),
                "english_name": ("نام انگلیسی", False),
                "detail_url": ("صفحه جزئیات", False),
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
                name="Dr-Koja — public drug index",
                source=source,
                defaults={
                    "start_url": url,
                    "entity_type": entity,
                    "parser_version": "1.0.0",
                    "extraction_config": {
                        "adapter": "dr_koja",
                        "max_records": 100,
                    },
                },
            )
            scraper.start_url = url
            scraper.entity_type = entity
            scraper.parser_version = "1.0.0"
            scraper.active = True
            scraper.save(update_fields=[
                "start_url", "entity_type", "parser_version", "active",
                "extraction_config",
            ])

            capture = capture_url(source, url)
            if capture.status != capture.Status.SUCCESS:
                return source, scraper, capture, []

            items = extract_drugs(capture.body, url)[:100]
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
                                "selector": "a[href^='/drug/']",
                                "value": item["name"],
                            },
                            {
                                "field": "detail_url",
                                "selector": "a[href^='/drug/']",
                                "value": item["detail_url"],
                            },
                        ],
                        "source_domain": source.domain,
                    }
                    for item in items
                ],
                fields=list(entity.fields.all()),
                batch_size=100,
            )
            return source, scraper, capture, records

        if persist:
            source, scraper, capture, records = run_once()
            rolled_back = False
        else:
            holder = {}
            try:
                with transaction.atomic():
                    holder["value"] = run_once()
                    raise DryRunRollback
            except DryRunRollback:
                pass
            source, scraper, capture, records = holder["value"]
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
            raise CommandError(capture.error_message or "Dr-Koja source was not fetched")
        if not records:
            raise CommandError("Dr-Koja parser extracted zero drug records")
