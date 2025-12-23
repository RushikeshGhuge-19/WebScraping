"""Pagination by path segments, e.g., /used-cars/page/2

Extracts next page links where pages use path-based numbering.
"""
from __future__ import annotations

from typing import List, Dict, Any
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base import CarTemplate

_PAGE_PATH_RE = re.compile(r'/page/(\d+)', re.I)


class PaginationPathTemplate(CarTemplate):
    name = 'pagination_path'

    def get_next_page(self, html: str, page_url: str) -> str | None:
        soup = BeautifulSoup(html, 'lxml')

        # Prefer rel=next
        link = soup.find('a', rel=lambda x: x and 'next' in x.lower())
        if link:
            href = link.get('href')
            if href:
                return urljoin(page_url, href)

        # Find hrefs containing /page/NUMBER
        for a in soup.find_all('a', href=True):
            if _PAGE_PATH_RE.search(a['href']):
                return urljoin(page_url, a['href'])
        return None

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        raise NotImplementedError()

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        raise NotImplementedError()
