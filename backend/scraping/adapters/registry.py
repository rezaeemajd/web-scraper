from scraping.adapters.darukade_product import extract_products as extract_darukade_products
from scraping.adapters.generic_jsonld import extract_jsonld_products
from scraping.adapters.pillix_pharmacy import extract_pharmacies as extract_pillix_pharmacies


ADAPTERS = {
    "generic": extract_jsonld_products,
    "darukade": extract_darukade_products,
    "pillix_pharmacy": extract_pillix_pharmacies,
}


def get_adapter(name):
    try:
        return ADAPTERS[name]
    except KeyError as exc:
        raise ValueError(f"unknown scraping adapter: {name}") from exc
