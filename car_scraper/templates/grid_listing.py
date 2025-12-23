"""Grid / image-first listing pattern.

Extracts detail links from listing pages that use image containers
like <div class="listing__image"> or similar.
"""
from __future__ import annotations

from typing import List, Dict, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base import CarTemplate

# Combined CSS selectors
_GRID_SELECTORS = 'div.listing__image, div.listing-image, div.image, div.stocklist-vehicle a.vehicleLink[href]'


class GridListingTemplate(CarTemplate):
    name = 'grid_listing'

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        soup = BeautifulSoup(html, 'lxml')
        urls: List[str] = []

        for el in soup.select(_GRID_SELECTORS):
            if el.name == 'a':
                href = el.get('href')
                if href:
                    urls.append(urljoin(page_url, href))
            else:
                a = el.find('a', href=True)
                if a:
                    urls.append(urljoin(page_url, a['href']))

        # Fallback: images with parent links
        for img in soup.find_all('img'):
            parent = img.find_parent('a')
            if parent:
                href = parent.get('href')
                if href:
                    urls.append(urljoin(page_url, href))

        return list(dict.fromkeys(urls))

    def get_next_page(self, html: str, page_url: str) -> str | None:
        return None

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        raise NotImplementedError()
