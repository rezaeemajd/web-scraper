from scraping.adapters.darukade_product import extract_products as extract_darukade_products
from scraping.adapters.generic_jsonld import extract_jsonld_products


ADAPTERS = {
    "generic": extract_jsonld_products,
    "darukade": extract_darukade_products,
}


def get_adapter(name):
    try:
        return ADAPTERS[name]
    except KeyError as exc:
        raise ValueError(f"unknown scraping adapter: {name}") from exc
