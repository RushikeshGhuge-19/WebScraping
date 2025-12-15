"""Pagination by path segments, e.g., /used-cars/page/2

Extracts next page links where pages use path-based numbering.
"""
from typing import Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base import CarTemplate
import re

_PAGE_PATH_RE = re.compile(r'/page/(\d+)', re.I)


class PaginationPathTemplate(CarTemplate):
    name = 'pagination_path'

    def get_next_page(self, html: str, page_url: str) -> Optional[str]:
        soup = BeautifulSoup(html, 'lxml')
        # prefer rel=next
        link = soup.find('a', rel=lambda x: x and 'next' in x.lower())
        if link and link.get('href'):
            return urljoin(page_url, link['href'])

        # find hrefs containing /page/NUMBER
        for a in soup.find_all('a', href=True):
            if _PAGE_PATH_RE.search(a['href']):
                return urljoin(page_url, a['href'])
        return None

    def get_listing_urls(self, html: str, page_url: str):
        raise NotImplementedError()

    def parse_car_page(self, html: str, car_url: str):
        raise NotImplementedError()
