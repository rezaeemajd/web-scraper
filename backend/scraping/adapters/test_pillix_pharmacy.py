from scraping.adapters.pillix_pharmacy import extract_pharmacies


def test_extract_pharmacies_reads_explicit_directory_fields():
    html = """
    <div class="card">
      <h2>داروخانه 29 فروردین (شهر تهران)</h2>
      <div>شبانه‌روزی</div>
      <div>استان : تهران</div>
      <div>شهرستان : تهران</div>
      <div>آدرس: میدان حر جنب آمادگاه بهداری 501 تهران</div>
    </div>
    <div class="card">
      <h2>داروخانه دکتر محمدرضا فرخ (شهر تهران)</h2>
      <div>روزانه</div>
      <div>استان : تهران</div>
      <div>شهرستان : تهران</div>
      <div>آدرس: تهران، رسالت، محله اوقاف</div>
    </div>
    """

    records = extract_pharmacies(html, "https://pillix.ir/pharmacy/county-tehran")

    assert len(records) == 2
    assert records[0]["name"].startswith("داروخانه 29 فروردین")
    assert records[0]["province"] == "تهران"
    assert records[0]["city"] == "تهران"
    assert records[0]["address"] == "میدان حر جنب آمادگاه بهداری 501 تهران"
    assert records[0]["pharmacy_type"] == "شبانه‌روزی"


def test_extract_pharmacies_deduplicates_repeated_cards():
    html = """
    <div><h2>داروخانه الف</h2><span>روزانه</span>
      <span>استان: تهران</span><span>شهرستان: تهران</span>
      <span>آدرس: خیابان نمونه</span></div>
    <div><h2>داروخانه الف</h2><span>روزانه</span>
      <span>استان: تهران</span><span>شهرستان: تهران</span>
      <span>آدرس: خیابان نمونه</span></div>
    """
    assert len(extract_pharmacies(html, "https://pillix.ir/pharmacy/county-tehran")) == 1


def test_extract_pharmacies_does_not_infer_availability():
    html = """
    <div><h2>داروخانه گارداسیل</h2>
      <span>استان: تهران</span><span>شهرستان: تهران</span>
      <span>آدرس: خیابان نمونه</span></div>
    """
    records = extract_pharmacies(html, "https://pillix.ir/pharmacy/county-tehran")
    assert records[0]["name"] == "داروخانه گارداسیل"
    assert "availability" not in records[0]
