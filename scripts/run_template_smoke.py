import sys
from pathlib import Path

# Add project root to path so car_scraper package imports work
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from car_scraper.templates import ALL_TEMPLATES
from car_scraper.templates import ListingJSONAPITemplate, ListingAjaxInfiniteTemplate, DetailImageGallery

print('ALL_TEMPLATES names:', [cls.name for cls in ALL_TEMPLATES])

html_json = '<html><script type="application/json">{"items":[{"url":"/car/123","title":"X"}]}</script></html>'
print('json_api ->', ListingJSONAPITemplate().get_listing_urls(html_json, 'https://example.com'))

html_ajax = '<html><script>fetch("/api/listing?page=2")</script><a href="/used-cars?page=3">more</a></html>'
print('ajax ->', ListingAjaxInfiniteTemplate().get_listing_urls(html_ajax, 'https://example.com'))

html_gallery = '<html><script type="application/ld+json">{"@type":"Product","image":["/img1.jpg","/img2.jpg"]}</script><img src="/thumb.jpg" data-large="/large.jpg"/></html>'
print('gallery ->', DetailImageGallery().parse_car_page(html_gallery, 'https://example.com/detail/1'))
