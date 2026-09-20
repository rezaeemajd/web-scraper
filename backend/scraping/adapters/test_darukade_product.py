from scraping.adapters.darukade_product import extract_products


def test_extract_products_keeps_retail_price_and_provenance():
    html = """
    <div>
      <a href="/products/vitamin-1">ویتامین د 1000</a>
      <a href="/brand/x">Brand X</a>
      <span>425,000 تومان</span>
    </div>
    <div>
      <a href="/products/vitamin-2">ویتامین سی</a>
      <span>390,000 تومان</span>
    </div>
    """
    items = extract_products(html, "https://darukade.com/products")

    assert len(items) == 2
    assert items[0]["name"] == "ویتامین د 1000"
    assert items[0]["price_text"] == "425,000 تومان"
    assert items[0]["detail_url"] == "https://darukade.com/products/vitamin-1"
    assert items[0]["observation_type"] == "retail_listing"


def test_extract_products_deduplicates_same_detail_url():
    html = """
    <a href="/products/a">آ</a>
    <a href="/products/a">آ</a>
    <a href="/products/b">ب</a>
    """
    assert len(extract_products(html, "https://darukade.com/products")) == 2
