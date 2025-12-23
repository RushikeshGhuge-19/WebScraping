"""Pagination by query parameter, e.g., ?page=2

This template focuses only on recognizing and constructing next-page URLs
using a `page` query parameter.
"""
from __future__ import annotations

from typing import List, Dict, Any
from urllib.parse import urlparse, urlencode, urlunparse, parse_qsl
from bs4 import BeautifulSoup
from .base import CarTemplate


class PaginationQueryTemplate(CarTemplate):
    name = 'pagination_query'

    def get_next_page(self, html: str, page_url: str) -> str | None:
        soup = BeautifulSoup(html, 'lxml')

        # Try rel=next
        link = soup.find('a', rel=lambda x: x and 'next' in x.lower())
        if link:
            href = link.get('href')
            if href:
                return href

        # Fallback: find any link with ?page= in href
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '?page=' in href or '&page=' in href:
                return href

        # Last resort: increment page parameter on current URL
        parsed = urlparse(page_url)
        qs = dict(parse_qsl(parsed.query or ''))
        if 'page' in qs:
            try:
                cur = int(qs['page'])
                qs['page'] = str(cur + 1)
                return urlunparse(parsed._replace(query=urlencode(qs)))
            except ValueError:
                pass
        return None

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        raise NotImplementedError()

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        raise NotImplementedError()
