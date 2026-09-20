import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from scraping.source_catalog import SOURCE_SEEDS
from sources.fetcher import capture_url
from sources.models import Source


class DryRunRollback(Exception):
    pass


class Command(BaseCommand):
    help = "Probe multiple curated Iranian healthcare sources through CDI Safe Fetch."

    def add_arguments(self, parser):
        parser.add_argument("--source", action="append", dest="sources")
        parser.add_argument("--persist", action="store_true")

    def handle(self, *args, **options):
        selected = options.get("sources")
        seeds = [
            item for item in SOURCE_SEEDS
            if not selected or item["key"] in set(selected)
        ]
        if selected and len(seeds) != len(set(selected)):
            known = {item["key"] for item in SOURCE_SEEDS}
            unknown = sorted(set(selected) - known)
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

                source_results = []
                for url in item["seeds"]:
                    capture = capture_url(source, url)
                    source_results.append({
                        "url": url,
                        "status": capture.status,
                        "status_code": capture.status_code,
                        "bytes": len(capture.body.encode("utf-8")),
                        "error": capture.error_message,
                    })
                results.append({
                    "source": item["key"],
                    "domain": item["domain"],
                    "capabilities": item["capabilities"],
                    "adapter": item["adapter"],
                    "captures": source_results,
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
            "seed_urls_checked": sum(len(item["captures"]) for item in results),
            "successful_captures": successful,
            "persisted": options["persist"],
            "rolled_back": rolled_back,
            "sources": results,
        }
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))

        if not results:
            raise CommandError("no source seeds selected")
