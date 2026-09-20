""""Curated public-source seeds for CDI discovery.

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
        "adapter": "pillix",
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
        "adapter": "dr_koja",
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
]
"