"""Section-based results listing.

Targets pages where listings are wrapped in a <section class="results-...">.
"""
from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base import CarTemplate


class SectionListingTemplate(CarTemplate):
    name = 'section_listing'

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        soup = BeautifulSoup(html, 'lxml')
        urls = []
        for section in soup.select('section.results-vehicleresults, section.results, section.listings'):
            for a in section.find_all('a', href=True):
                urls.append(urljoin(page_url, a['href']))
        return list(dict.fromkeys(urls))

    def get_next_page(self, html: str, page_url: str):
        return None

    def parse_car_page(self, html: str, car_url: str):
        raise NotImplementedError()
