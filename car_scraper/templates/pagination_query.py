"""Pagination by query parameter, e.g., ?page=2

This template focuses only on recognizing and constructing next-page URLs
using a `page` query parameter.
"""
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, parse_qsl
from .base import CarTemplate
from bs4 import BeautifulSoup


class PaginationQueryTemplate(CarTemplate):
    name = 'pagination_query'

    def get_next_page(self, html: str, page_url: str) -> Optional[str]:
        # Try rel=next
        soup = BeautifulSoup(html, 'lxml')
        link = soup.find('a', rel=lambda x: x and 'next' in x.lower())
        if link and link.get('href'):
            return link['href']

        # Fallback: find any link with ?page= in href
        for a in soup.find_all('a', href=True):
            if '?page=' in a['href'] or '&page=' in a['href']:
                return a['href']

        # As a last resort, try to increment page parameter on current URL
        parsed = urlparse(page_url)
        qs = dict(parse_qsl(parsed.query or ''))
        if 'page' in qs:
            try:
                cur = int(qs['page'])
                qs['page'] = str(cur + 1)
                new_query = urlencode(qs)
                return urlunparse(parsed._replace(query=new_query))
            except Exception:
                return None
        return None

    def get_listing_urls(self, html: str, page_url: str):
        raise NotImplementedError()

    def parse_car_page(self, html: str, car_url: str):
        raise NotImplementedError()
