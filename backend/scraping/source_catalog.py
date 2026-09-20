"""Curated public-source seeds for CDI discovery.

This is intentionally source-first: CDI must discover and crawl across multiple
independent domains, not treat one URL as the market. Seeds are only entry
points; adapters and link discovery expand coverage within each allowed domain.
"""

SOURCE_SEEDS = [
    {
        "key": "pillix",
        "name": "Pillix",
        "domain": "pillix.ir",
        "base_url": "https://pillix.ir",
        "seeds": [
            "https://pillix.ir/medicine",
            "https://pillix.ir/pharmacy/province-tehran",
            "https://pillix.ir/pharmacy/county-tehran",
        ],
        "capabilities": ["drug", "pharmacy", "market_search"],
        "adapter": "generic",
    },
    {
        "key": "darooha",
        "name": "Darooha",
        "domain": "darooha.com",
        "base_url": "https://www.darooha.com",
        "seeds": ["https://www.darooha.com/"],
        "capabilities": ["drug", "pharmacy", "market_search"],
        "adapter": "generic",
    },
    {
        "key": "darukhane",
        "name": "DarukhaneYab",
        "domain": "darukhane.app",
        "base_url": "https://www.darukhane.app",
        "seeds": ["https://www.darukhane.app/"],
        "capabilities": ["pharmacy", "drug"],
        "adapter": "generic",
    },
    {
        "key": "dr_koja",
        "name": "Dr-Koja",
        "domain": "dr-koja.ir",
        "base_url": "https://dr-koja.ir",
        "seeds": ["https://dr-koja.ir/drugs"],
        "capabilities": ["drug", "doctor", "clinic"],
        "adapter": "generic",
    },
    {
        "key": "boroshor",
        "name": "Boroshor",
        "domain": "boroshor.ir",
        "base_url": "https://boroshor.ir",
        "seeds": ["https://boroshor.ir/"],
        "capabilities": ["drug", "leaflet", "manufacturer"],
        "adapter": "generic",
    },
    {
        "key": "digikala",
        "name": "Digikala",
        "domain": "digikala.com",
        "base_url": "https://www.digikala.com",
        "seeds": ["https://www.digikala.com/"],
        "capabilities": [
            "retail_product",
            "retail_price",
            "health_product",
            "medical_equipment",
            "supplement",
        ],
        "adapter": "generic",
    },
    {
        "key": "digikala_pharmacy",
        "name": "Digikala Pharmacy",
        "domain": "pharmacy.digikala.com",
        "base_url": "https://pharmacy.digikala.com",
        "seeds": ["https://pharmacy.digikala.com/"],
        "capabilities": ["retail_product", "retail_price", "health_product"],
        "adapter": "generic",
    },
    {
        "key": "torob",
        "name": "Torob",
        "domain": "torob.com",
        "base_url": "https://torob.com",
        "seeds": ["https://torob.com/"],
        "capabilities": ["marketplace", "retail_product", "retail_price", "health_product"],
        "adapter": "generic",
    },
    {
        "key": "iran_supp",
        "name": "Iran Supplement",
        "domain": "iran-supp.com",
        "base_url": "https://iran-supp.com",
        "seeds": [
            "https://iran-supp.com/product/gardasil-9-turkey/",
            "https://iran-supp.com/product/usa-gardasil-9/",
        ],
        "capabilities": ["retail_product", "retail_price", "health_product"],
        "adapter": "generic",
    },
    {
        "key": "pharmaweb",
        "name": "PharmaWeb",
        "domain": "medpharmaweb.com",
        "base_url": "https://medpharmaweb.com",
        "seeds": [
            "https://www.medpharmaweb.com/item/gardasil_groups_gardasil_gardasil9/",
            "https://www.medpharmaweb.com/item/gardasil_groups_gardasil_gardasil9s/",
        ],
        "capabilities": ["retail_product", "retail_price", "health_product", "pharmacy"],
        "adapter": "generic",
    },
    {
        "key": "darukade",
        "name": "Darukade",
        "domain": "darukade.com",
        "base_url": "https://darukade.com",
        "seeds": ["https://darukade.com/products"],
        "capabilities": ["retail_product", "retail_price", "brand", "pharmacy"],
        "adapter": "darukade",
    },
]
