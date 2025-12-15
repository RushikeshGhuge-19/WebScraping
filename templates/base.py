class CarTemplate:
    """
    Base interface for all car dealer templates.
    """

    name = "base"

    def get_listing_urls(self, html, page_url):
        raise NotImplementedError

    def get_next_page(self, html, page_url):
        return None

    def parse_car_page(self, html, car_url):
        raise NotImplementedError
