import json

import pytest

from datahub.models import EntityType, ExtractedRecord

from .engine import build_export
from .models import ExportJob


@pytest.mark.django_db
@pytest.mark.parametrize("fmt", [
    ExportJob.Format.CSV,
    ExportJob.Format.XLSX,
    ExportJob.Format.JSON,
    ExportJob.Format.JSONL,
    ExportJob.Format.TXT,
    ExportJob.Format.DOCX,
    ExportJob.Format.PDF,
])
def test_build_export_supports_all_formats(tmp_path, settings, fmt):
    settings.EXPORT_ROOT = str(tmp_path)
    entity = EntityType.objects.create(name="دارو", slug="drug-export")
    ExtractedRecord.objects.create(
        entity_type=entity,
        source_url="https://example.com/drug/1",
        source_domain="example.com",
        payload={"name": "آسپرین", "price": 12000},
        normalized_payload={"name": "آسپرین", "price": 12000},
        evidence=[],
        fingerprint="f" * 64,
    )
    job = ExportJob.objects.create(format=fmt, filters={})

    path = build_export(job)

    assert path.is_file()
    assert path.stat().st_size > 0
    if fmt == ExportJob.Format.JSON:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data[0]["source_domain"] == "example.com"
