import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from datahub.models import EntityField, EntityType
from datahub.pharmacy_pipeline import upsert_pharmacy_from_record
from datahub.pipeline import process_records
from scraping.adapters.pillix_pharmacy import extract_pharmacies
from sources.fetcher import capture_url
from sources.models import Source


DEFAULT_URL = "https://pillix.ir/pharmacy/county-tehran"
DEFAULT_DOMAIN = "pillix.ir"


class DryRunRollback(Exception):
    pass


class Command(BaseCommand):
    help = "Run a bounded real-world Pillix pharmacy directory crawl."

    def add_arguments(self, parser):
        parser.add_argument("--url", default=DEFAULT_URL)
        parser.add_argument("--domain", default=DEFAULT_DOMAIN)
        parser.add_argument("--persist", action="store_true")
        parser.add_argument("--max-pages", type=int, default=1)

    def handle(self, *args, **options):
        url = options["url"]
        domain = options["domain"]
        persist = options["persist"]
        max_pages = options["max_pages"]

        if not 1 <= max_pages <= 3:
            raise CommandError("--max-pages must be between 1 and 3")

        def run_once():
            source, _ = Source.objects.get_or_create(
                domain=domain,
                defaults={
                    "name": "Pillix pharmacy directory",
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
            source.save(update_fields=[
                "base_url",
                "respect_robots",
                "rate_limit_per_minute",
                "max_response_bytes",
            ])

            entity, _ = EntityType.objects.get_or_create(
                slug="pharmacy",
                defaults={
                    "name": "داروخانه",
                    "description": "Real-world pharmacy directory records.",
                },
            )
            fields = {
                "name": ("نام داروخانه", True),
                "province": ("استان", True),
                "city": ("شهرستان", True),
                "district": ("منطقه", False),
                "address": ("آدرس", True),
                "pharmacy_type": ("نوع فعالیت", False),
                "service_hours": ("ساعات خدمت", False),
                "public_phone": ("تلفن عمومی", False),
                "website": ("وب‌سایت", False),
            }
            for position, (slug, (name, identifier)) in enumerate(fields.items()):
                EntityField.objects.get_or_create(
                    entity_type=entity,
                    slug=slug,
                    defaults={
                        "name": name,
                        "is_identifier": identifier,
                        "is_blocking": identifier,
                        "searchable": True,
                        "position": position,
                    },
                )

            captures = []
            records = []
            pharmacies = []
            current_url = url
            visited = set()

            import httpx

            with httpx.Client(
                timeout=httpx.Timeout(20.0, connect=10.0),
                follow_redirects=False,
                trust_env=False,
                headers={"User-Agent": source.user_agent},
            ) as client:
                for _ in range(max_pages):
                    if current_url in visited:
                        break
                    visited.add(current_url)
                    capture = capture_url(source, current_url, client=client)
                    captures.append(capture)
                    if capture.status != capture.Status.SUCCESS:
                        break
                    if capture.pk is None:
                        capture.save()

                    items = extract_pharmacies(capture.body, current_url)
                    payload_items = [
                        {
                            "url": item["source_url"],
                            "payload": item,
                            "raw_capture": capture,
                            "evidence": [
                                {
                                    "field": "directory_card",
                                    "selector": "h2",
                                    "value": item["name"],
                                    "source_url": current_url,
                                }
                            ],
                            "source_domain": source.domain,
                        }
                        for item in items
                    ]
                    page_records = process_records(
                        entity_type=entity,
                        items=payload_items,
                        fields=list(entity.fields.all()),
                        batch_size=100,
                    )
                    records.extend(page_records)
                    for record in page_records:
                        pharmacies.append(upsert_pharmacy_from_record(record))

                    # This first bounded command intentionally follows only the
                    # adapter's explicit page URL; pagination can be added once
                    # the live directory semantics are verified.
                    break

            return source, captures, records, pharmacies

        if persist:
            source, captures, records, pharmacies = run_once()
            rolled_back = False
        else:
            holder = {}
            try:
                with transaction.atomic():
                    holder["value"] = run_once()
                    raise DryRunRollback
            except DryRunRollback:
                pass
            source, captures, records, pharmacies = holder["value"]
            rolled_back = True

        result = {
            "source": domain,
            "url": url,
            "captures": len(captures),
            "capture_statuses": [capture.status for capture in captures],
            "records": len(records),
            "pharmacies": len(pharmacies),
            "persisted": persist,
            "rolled_back": rolled_back,
            "market_observations_created": 0,
            "sample": [
                {
                    "name": pharmacy.name,
                    "province": pharmacy.location.province if pharmacy.location else "",
                    "city": pharmacy.location.city if pharmacy.location else "",
                    "address": pharmacy.location.address if pharmacy.location else "",
                    "type": pharmacy.pharmacy_type,
                    "source_url": pharmacy.source_url,
                }
                for pharmacy in pharmacies[:5]
            ],
        }
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))

        if not captures:
            raise CommandError("no pharmacy directory capture was produced")
        if captures[0].status != captures[0].Status.SUCCESS:
            raise CommandError(captures[0].error_message or "pharmacy directory fetch failed")
        if not records:
            raise CommandError("pharmacy directory extraction produced zero records")
        if len(records) != len(pharmacies):
            raise CommandError("pharmacy materialization count does not match extracted records")
