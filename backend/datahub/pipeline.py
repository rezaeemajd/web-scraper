import hashlib, json
from decimal import Decimal
from django.db import IntegrityError
from urllib.parse import urlsplit
from .models import ExtractedRecord

def normalize_text(value):
    if not isinstance(value,str): return value
    return " ".join(value.replace("ي","ی").replace("ى","ی").replace("ك","ک").replace("ۀ","هٔ").split())
def normalize_value(value):
    if isinstance(value,dict): return {str(k): normalize_value(v) for k,v in value.items()}
    if isinstance(value,list): return [normalize_value(v) for v in value]
    return normalize_text(value)
def canonical_url(url):
    p=urlsplit(url); scheme=p.scheme.lower(); host=(p.hostname or "").lower(); path=p.path or "/"; path=path.rstrip("/") or "/"; return f"{scheme}://{host}{path}"+((("?"+p.query)) if p.query else "")
def fingerprint(payload):
    raw=json.dumps(normalize_value(payload),ensure_ascii=False,sort_keys=True,separators=(",",":")); return hashlib.sha256(raw.encode()).hexdigest()
def validate_payload(entity_type,payload):
    return [{"field":f.slug,"code":"required"} for f in entity_type.fields.all() if f.required and payload.get(f.slug) in (None,"",[])]
def quality_score(payload,entity_type,errors):
    fields=list(entity_type.fields.all())
    if not fields: return Decimal("0.0000")
    filled=sum(1 for f in fields if payload.get(f.slug) not in (None,"",[])); return Decimal(str(round(max(0.0,filled/len(fields)-min(0.5,len(errors)*0.1)),4)))
def process_record(*,entity_type,url,payload,raw_capture=None,evidence=None,source_domain=None):
    normalized=normalize_value(payload)
    fields = list(entity_type.fields.all())
    errors=validate_payload(entity_type,normalized,fields=fields)
    score=quality_score(normalized,entity_type,errors,fields=fields)
    values={
        "raw_capture":raw_capture,
        "source_url":canonical_url(url),
        "source_domain":source_domain or (urlsplit(url).hostname or "").lower(),
        "payload":payload,
        "normalized_payload":normalized,
        "evidence":evidence or [],
        "confidence":score,
        "quality_score":score,
        "fingerprint":fingerprint(normalized),
        "validation_errors":errors,
        "status":ExtractedRecord.Status.REVIEW if errors else ExtractedRecord.Status.PARSED,
    }
    try:
        record, _ = ExtractedRecord.objects.get_or_create(
            entity_type=entity_type,
            fingerprint=values["fingerprint"],
            defaults=values,
        )
    except IntegrityError:
        record = ExtractedRecord.objects.get(
            entity_type=entity_type,
            fingerprint=values["fingerprint"],
        )
    return record
