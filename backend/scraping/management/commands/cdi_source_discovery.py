import json

import httpx
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from scraping.adapters.registry import get_adapter
from scraping.discovery import bounded_discovery
from scraping.source_catalog import SOURCE_SEEDS
from sources.fetcher import capture_url
from sources.models import Source


class DryRunRollback(Exception):
    pass


class Command(BaseCommand):
    help = "Run bounded same-domain discovery across curated healthcare sources."

    def add_arguments(self, parser):
        parser.add_argument("--source", action="append", dest="sources")
        parser.add_argument("--persist", action="store_true")
        parser.add_argument("--max-pages", type=int, default=3)
        parser.add_argument("--max-urls", type=int, default=25)

    def handle(self, *args, **options):
        selected = options.get("sources")
        if options["max_pages"] < 1 or options["max_pages"] > 100:
            raise CommandError("--max-pages must be between 1 and 100")
        if options["max_urls"] < 1 or options["max_urls"] > 500:
            raise CommandError("--max-urls must be between 1 and 500")

        selected_keys = set(selected or [])
        seeds = [
            item for item in SOURCE_SEEDS
            if not selected or item["key"] in selected_keys
        ]
        if selected and len(seeds) != len(selected_keys):
            known = {item["key"] for item in SOURCE_SEEDS}
            unknown = sorted(selected_keys - known)
            raise CommandError(f"unknown source(s): {', '.join(unknown)}")

        def run_once():
            results = []
            for item in seeds:
                source, _ = Source.objects.get_or_create(
                    domain=item["domain"],
                    defaults={
                        "name": item["name"],
                        "base_url": item["base_url"],
                        "respect_robots": True,
                        "rate_limit_per_minute": 10,
                        "max_response_bytes": 5 * 1024 * 1024,
                    },
                )
                source.name = item["name"]
                source.base_url = item["base_url"]
                source.respect_robots = True
                source.rate_limit_per_minute = max(1, source.rate_limit_per_minute or 10)
                source.max_response_bytes = min(
                    max(64 * 1024, source.max_response_bytes or 5 * 1024 * 1024),
                    5 * 1024 * 1024,
                )
                source.save(update_fields=[
                    "name",
                    "base_url",
                    "respect_robots",
                    "rate_limit_per_minute",
                    "max_response_bytes",
                ])

                with httpx.Client(
                    timeout=httpx.Timeout(20.0, connect=10.0),
                    follow_redirects=False,
                    trust_env=False,
                    headers={"User-Agent": source.user_agent},
                ) as client:
                    def fetch_page(url):
                        try:
                            return capture_url(source, url, client=client)
                        except TypeError as exc:
                            if "unexpected keyword argument 'client'" not in str(exc):
                                raise
                            return capture_url(source, url)

                    pages = bounded_discovery(
                        source,
                        item["seeds"],
                        fetch_page,
                        max_pages=options["max_pages"],
                        max_urls=options["max_urls"],
                        is_success=lambda capture: capture.status == capture.Status.SUCCESS,
                    )

                adapter = get_adapter(item["adapter"])
                captures = []
                extracted_records = 0
                extraction_errors = []
                for url, capture in pages:
                    entry = {
                        "url": url,
                        "status": capture.status,
                        "status_code": capture.status_code,
                        "bytes": len(capture.body.encode("utf-8")),
                        "error": capture.error_message,
                        "extracted_records": 0,
                    }
                    if capture.status == capture.Status.SUCCESS:
                        try:
                            records = adapter(capture.body, url)
                            entry["extracted_records"] = len(records)
                            extracted_records += len(records)
                        except Exception as exc:
                            entry["extraction_error"] = str(exc)[:500]
                            extraction_errors.append(
                                {"url": url, "error": str(exc)[:500]}
                            )
                    captures.append(entry)
                results.append({
                    "source": item["key"],
                    "domain": item["domain"],
                    "capabilities": item["capabilities"],
                    "adapter": item["adapter"],
                    "pages_discovered_and_fetched": len(pages),
                    "records_extracted": extracted_records,
                    "extraction_errors": extraction_errors,
                    "captures": captures,
                })
            return results

        if options["persist"]:
            results = run_once()
            rolled_back = False
        else:
            holder = {}
            try:
                with transaction.atomic():
                    holder["results"] = run_once()
                    raise DryRunRollback
            except DryRunRollback:
                pass
            results = holder["results"]
            rolled_back = True

        successful = sum(
            1
            for item in results
            for capture in item["captures"]
            if capture["status"] == "success"
        )
        result = {
            "sources_checked": len(results),
            "pages_checked": sum(
                len(item["captures"]) for item in results
            ),
            "successful_captures": successful,
            "max_pages_per_source": options["max_pages"],
            "max_urls_per_source": options["max_urls"],
            "persisted": options["persist"],
            "rolled_back": rolled_back,
            "sources": results,
        }
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))

        if not results:
            raise CommandError("no source seeds selected")
