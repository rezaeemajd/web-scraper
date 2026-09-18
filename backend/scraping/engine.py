from selectolax.parser import HTMLParser
from .models import Scraper
from sources.fetcher import capture_url
from datahub.pipeline import process_record

def extract_static_html(scraper:Scraper,html:str):
    config=scraper.extraction_config or {}
    payload={}; evidence=[]; tree=HTMLParser(html)
    for field,selector in (config.get("fields") or {}).items():
        node=tree.css_first(selector)
        value=node.text(strip=True) if node else ""
        payload[field]=value
        evidence.append({"field":field,"selector":selector,"value":value})
    return payload,evidence

def execute(scraper:Scraper):
    if not scraper.entity_type: raise ValueError("scraper.entity_type is required")
    capture=capture_url(scraper.source,scraper.start_url)
    if capture.status != capture.Status.SUCCESS: return None,capture
    payload,evidence=extract_static_html(scraper,capture.body)
    return process_record(entity_type=scraper.entity_type,url=scraper.start_url,payload=payload,raw_capture=capture,evidence=evidence,source_domain=scraper.source.domain),capture
