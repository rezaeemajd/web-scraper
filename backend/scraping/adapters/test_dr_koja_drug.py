import pytest

from scraping.adapters.dr_koja_drug import extract_drugs


def test_extract_drugs_uses_drug_detail_links_and_keeps_provenance():
    html = """
    <section class="drug-card">
      <a href="/drug/استامینوفن-123">استامینوفن</a>
      <p>Acetaminophen</p>
    </section>
    <section class="drug-card">
      <a href="/drug/ایبوپروفن-456">ایبوپروفن</a>
      <p>Ibuprofen</p>
    </section>
    """
    items = extract_drugs(html, "https://dr-koja.ir/drugs?page=2")

    assert items == [
        {
            "name": "استامینوفن",
            "english_name": "Acetaminophen",
            "detail_url": "https://dr-koja.ir/drug/استامینوفن-123",
            "source_url": "https://dr-koja.ir/drugs?page=2",
        },
        {
            "name": "ایبوپروفن",
            "english_name": "Ibuprofen",
            "detail_url": "https://dr-koja.ir/drug/ایبوپروفن-456",
            "source_url": "https://dr-koja.ir/drugs?page=2",
        },
    ]


def test_extract_drugs_ignores_non_drug_links_and_duplicate_cards():
    html = """
    <a href="/doctor/1">پزشک</a>
    <div><a href="/drug/aspirin-1">آسپرین</a><span>Aspirin</span></div>
    <div><a href="/drug/aspirin-1">آسپرین</a><span>Aspirin</span></div>
    <a href="https://example.com/drug/other">خارجی</a>
    """
    items = extract_drugs(html, "https://dr-koja.ir/drugs")

    assert len(items) == 1
    assert items[0]["detail_url"] == "https://dr-koja.ir/drug/aspirin-1"
    assert items[0]["english_name"] == "Aspirin"


def test_extract_drugs_requires_visible_name():
    html = '<a href="/drug/empty-1">   </a>'
    assert extract_drugs(html, "https://dr-koja.ir/drugs") == []
