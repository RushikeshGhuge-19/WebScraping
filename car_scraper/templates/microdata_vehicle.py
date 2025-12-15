"""Microdata-based Vehicle template.

Parses simple microdata (`itemscope` / `itemtype` / `itemprop`) for
vehicle information. Intended as a lightweight fallback when JSON-LD
isn't present but microdata marks exist.
"""
from typing import Dict, Any
from bs4 import BeautifulSoup
from .base import CarTemplate


class MicrodataVehicleTemplate(CarTemplate):
    name = 'microdata_vehicle'

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, 'lxml')
        out: Dict[str, Any] = {'_source': 'microdata'}

        # Find an itemscope with Vehicle in itemtype
        for tag in soup.find_all(attrs={"itemscope": True}):
            it = tag.get('itemtype') or ''
            if 'Vehicle' in it or 'vehicle' in it.lower():
                # extract common itemprops
                for prop in ('name', 'brand', 'model', 'description', 'price'):
                    node = tag.find(attrs={'itemprop': prop})
                    if node:
                        out[prop] = node.get_text(strip=True)
                # price could be in meta tag inside
                price_meta = tag.find('meta', attrs={'itemprop': 'price'})
                if price_meta and price_meta.get('content'):
                    out['price'] = price_meta['content']
                return out

        return out
