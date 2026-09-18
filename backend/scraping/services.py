from urllib.parse import urlparse
def same_domain(url, allowed_domain):
    return (urlparse(url).hostname or "").lower().lstrip("www.")==allowed_domain.lower().lstrip("www.")
