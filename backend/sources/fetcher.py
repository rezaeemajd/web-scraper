import hashlib
import urllib.robotparser
from urllib.parse import urlsplit
import httpx
from .models import Source
from datahub.models import RawCapture

class FetchBlocked(Exception): pass

def _same_domain(source,url):
    return (urlsplit(source.base_url).hostname or "").lower()==(urlsplit(url).hostname or "").lower()

def capture_url(source:Source,url:str)->RawCapture:
    if not source.allowed or source.status != Source.Status.ACTIVE: raise FetchBlocked("source is not active")
    if not _same_domain(source,url): raise FetchBlocked("url is outside source domain")
    if source.respect_robots:
        rp=urllib.robotparser.RobotFileParser(); robots_url=source.base_url.rstrip("/")+"/robots.txt"
        try:
            with httpx.Client(timeout=httpx.Timeout(5.0,connect=3.0),follow_redirects=True,headers={"User-Agent":source.user_agent}) as robots_client:
                rr=robots_client.get(robots_url)
            if rr.is_success: rp.parse(rr.text.splitlines())
        except Exception: pass
        if rp.default_entry is not None and not rp.can_fetch(source.user_agent,url):
            return RawCapture.objects.create(url=url,status=RawCapture.Status.BLOCKED,error_message="robots.txt disallowed")
    try:
        with httpx.Client(timeout=httpx.Timeout(20.0,connect=10.0),follow_redirects=True,headers={"User-Agent":source.user_agent}) as client:
            response=client.get(url)
            body=response.content[:source.max_response_bytes]
        text=body.decode(response.encoding or "utf-8",errors="replace")
        return RawCapture.objects.create(url=url,status_code=response.status_code,content_type=response.headers.get("content-type",""),body=text,headers=dict(response.headers),body_sha256=hashlib.sha256(body).hexdigest(),status=RawCapture.Status.SUCCESS if response.is_success else RawCapture.Status.ERROR)
    except Exception as exc:
        return RawCapture.objects.create(url=url,status=RawCapture.Status.ERROR,error_message=str(exc)[:2000])
