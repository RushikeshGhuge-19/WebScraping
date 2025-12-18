"""SUPPORTING MODULE — Meta tag helpers (NOT a structural template).

Parses common meta tags (Open Graph, product) for basic fields like
title, price, currency. These functions are intended as fallbacks for
DETAIL templates and are not part of the canonical structural template
set.
"""
from typing import Dict, Any
from bs4 import BeautifulSoup
from .base import CarTemplate


class MetaTagsTemplate(CarTemplate):
    name = 'meta_tags'

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, 'lxml')
        out: Dict[str, Any] = {'_source': 'meta'}

        def meta(name=None, prop=None):
            if prop:
                tag = soup.find('meta', attrs={'property': prop})
                if tag and tag.get('content'):
                    return tag['content']
            if name:
                tag = soup.find('meta', attrs={'name': name})
                if tag and tag.get('content'):
                    return tag['content']
            return None

        out['title'] = meta(prop='og:title') or meta(name='title') or soup.title.string if soup.title else None
        out['price'] = meta(prop='product:price:amount') or meta(name='price')
        out['currency'] = meta(prop='product:price:currency') or meta(name='currency')
        out['description'] = meta(prop='og:description') or meta(name='description')
        return out
