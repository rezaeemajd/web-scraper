import pytest
from .models import EntityField,EntityType
from .pipeline import canonical_url,normalize_value,process_record

@pytest.mark.django_db
def test_pipeline_normalizes_and_scores_required_fields():
    entity=EntityType.objects.create(name="دارو",slug="drug")
    EntityField.objects.create(entity_type=entity,name="نام",slug="name",required=True)
    EntityField.objects.create(entity_type=entity,name="برند",slug="brand",required=False)
    record=process_record(entity_type=entity,url="HTTPS://Example.COM/path/",payload={"name":" كالا  ","brand":"ب رند"})
    assert record.source_url=="https://example.com/path"
    assert record.normalized_payload["name"]=="کالا"
    assert record.quality_score==1
    assert record.validation_errors==[]

def test_canonical_url():
    assert canonical_url("HTTPS://Example.COM/a///?x=1")=="https://example.com/a?x=1"

def test_recursive_normalization():
    assert normalize_value({"x":[" ي ",{"y":"ك"}]})=={"x":["ی",{"y":"ک"}]}
