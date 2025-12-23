"""Section-based results listing.

Targets pages where listings are wrapped in a <section class="results-...">.
"""
from __future__ import annotations

from typing import List, Dict, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base import CarTemplate

# Combined section selectors
_SECTION_SELECTORS = 'section.results-vehicleresults, section.results, section.listings'


class SectionListingTemplate(CarTemplate):
    name = 'section_listing'

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        soup = BeautifulSoup(html, 'lxml')
        urls: List[str] = []

        for section in soup.select(_SECTION_SELECTORS):
            for a in section.find_all('a', href=True):
                urls.append(urljoin(page_url, a['href']))

        return list(dict.fromkeys(urls))

    def get_next_page(self, html: str, page_url: str) -> str | None:
        return None

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        raise NotImplementedError()
