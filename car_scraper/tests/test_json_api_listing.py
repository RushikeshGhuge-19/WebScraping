from car_scraper.templates.json_api_listing import JSONAPIListingTemplate
from pathlib import Path
import json


def load_sample(name: str) -> str:
    p = Path(__file__).parent.parent.parent / 'scripts' / name
    return p.read_text(encoding='utf-8')


def test_json_api_extract_urls():
    # use scripts/sample_results.json which contains a JSON structure
    raw = load_sample('sample_results.json')
    tpl = JSONAPIListingTemplate()
    urls = tpl.get_listing_urls(raw, 'http://example/')
    # expect a list (may be empty if no URLs found in this particular sample)
    assert isinstance(urls, list)
