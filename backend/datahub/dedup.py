from decimal import Decimal
from .models import DedupCandidate,ExtractedRecord

def similarity(a,b):
    keys=set(a) & set(b)
    if not keys: return Decimal("0.0000"),[]
    matches=[k for k in keys if a.get(k) not in (None,"") and a.get(k)==b.get(k)]
    return Decimal(str(round(len(matches)/len(keys),4))),matches

def find_candidates(record,limit=20):
    qs=ExtractedRecord.objects.filter(entity_type=record.entity_type).exclude(pk=record.pk).exclude(fingerprint=record.fingerprint)[:limit]
    created=[]
    for other in qs:
        score,fields=similarity(record.normalized_payload,other.normalized_payload)
        if score>=Decimal("0.7000"):
            obj,_=DedupCandidate.objects.get_or_create(record_a=min(record,other,key=lambda x:x.pk),record_b=max(record,other,key=lambda x:x.pk),defaults={"similarity":score,"matched_fields":fields})
            created.append(obj)
    return created
