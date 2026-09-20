import json

from scraping.adapters.generic_jsonld import extract_jsonld_products


def test_extract_jsonld_product_and_offer():
    html = f"""
    <script type="application/ld+json">
    {json.dumps({
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Gardasil 9",
        "brand": {"@type": "Brand", "name": "MSD"},
        "sku": "J07BM03",
        "offers": {
            "@type": "Offer",
            "url": "https://example.com/p/gardasil-9",
            "price": "12500000",
            "priceCurrency": "IRR",
            "availability": "https://schema.org/InStock",
        },
    })}
    </script>
    """
    records = extract_jsonld_products(html, "https://example.com/p/gardasil-9")

    assert records == [{
        "name": "Gardasil 9",
        "brand": "MSD",
        "sku": "J07BM03",
        "detail_url": "https://example.com/p/gardasil-9",
        "price": "12500000",
        "currency": "IRR",
        "availability": "instock",
        "source_url": "https://example.com/p/gardasil-9",
        "observation_type": "retail_product",
        "evidence_type": "schema.org/Product",
    }]


def test_invalid_jsonld_is_ignored():
    html = '<script type="application/ld+json">{not-json}</script>'
    assert extract_jsonld_products(html, "https://example.com/") == []
