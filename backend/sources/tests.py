from .fetcher import _same_domain


def test_same_domain_rejects_external_host():
    source = type("SourceStub", (), {"base_url": "https://example.com"})()
    assert _same_domain(source, "https://example.com/path")
    assert not _same_domain(source, "https://evil.example/path")
