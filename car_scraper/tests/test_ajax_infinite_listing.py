from car_scraper.templates.ajax_infinite_listing import AjaxInfiniteListingTemplate


def test_ajax_infinite_extracts_urls_and_next():
    # crafted HTML simulating an XHR-injected JSON blob
    html = '''
    <html><head></head><body>
    <script type="application/json">
    {"results": [{"url": "/vehicle/123"}, {"url": "https://example.com/car/456"}], "next": "/api/listings?page=2"}
    </script>
    </body></html>
    '''
    tpl = AjaxInfiniteListingTemplate()
    urls = tpl.get_listing_urls(html, 'http://example/')
    assert '/vehicle/123' in urls
    assert 'https://example.com/car/456' in urls
    nxt = tpl.get_next_page(html, 'http://example/')
    assert nxt == '/api/listings?page=2'
