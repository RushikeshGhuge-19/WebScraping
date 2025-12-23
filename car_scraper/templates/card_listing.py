"""Card-based listing pattern.

Extract links from card elements like <div class="vehicle-card">.
"""
from __future__ import annotations

from typing import List, Dict, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base import CarTemplate

# Combined CSS selectors for efficiency
_CARD_SELECTORS = '.vehicle-card, .car-card, .listing-card, div.stocklist-vehicle a.vehicleLink[href]'


class CardListingTemplate(CarTemplate):
    name = 'card_listing'

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        soup = BeautifulSoup(html, 'lxml')
        urls: List[str] = []

        for el in soup.select(_CARD_SELECTORS):
            # Check if element is already an anchor
            if el.name == 'a':
                href = el.get('href')
                if href:
                    urls.append(urljoin(page_url, href))
            else:
                # Find first anchor in card
                a = el.find('a', href=True)
                if a:
                    urls.append(urljoin(page_url, a['href']))

        return list(dict.fromkeys(urls))

    def get_next_page(self, html: str, page_url: str) -> str | None:
        return None

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        raise NotImplementedError()
