"""Canonical file `detail_jsonld_vehicle.py` — delegates to existing jsonld implementation.

This wrapper preserves the authoritative filename while reusing the
previous `JSONLDVehicleTemplate` implementation to avoid duplication.
"""
from typing import Dict, Any
from .jsonld_vehicle import JSONLDVehicleTemplate
from bs4 import BeautifulSoup
import html as _html


def _meta_fallback_from_html(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, 'lxml')
    out: Dict[str, Any] = {'_source': 'meta-fallback'}

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

    out['title'] = meta(prop='og:title') or meta(name='title') or (soup.title.string if soup.title else None)
    out['price'] = meta(prop='product:price:amount') or meta(name='price')
    out['currency'] = meta(prop='product:price:currency') or meta(name='currency')
    out['description'] = meta(prop='og:description') or meta(name='description')
    return out


def _microdata_fallback_from_html(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, 'lxml')
    out: Dict[str, Any] = {'_source': 'microdata-fallback'}
    for tag in soup.find_all(attrs={"itemscope": True}):
        it = tag.get('itemtype') or ''
        if 'Vehicle' in it or 'vehicle' in it.lower():
            for prop in ('name', 'brand', 'model', 'description', 'price'):
                node = tag.find(attrs={'itemprop': prop})
                if node:
                    out[prop] = node.get_text(strip=True)
            price_meta = tag.find('meta', attrs={'itemprop': 'price'})
            if price_meta and price_meta.get('content'):
                out['price'] = price_meta['content']
            return out
    return out


class DetailJSONLDVehicle(JSONLDVehicleTemplate):
    name = 'detail_jsonld_vehicle'

    # inherits parse_car_page from JSONLDVehicleTemplate
    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        out = super().parse_car_page(html, car_url)
        # If JSON-LD returned nothing useful, try microdata/meta fallbacks
        useful = bool(out.get('name') or out.get('brand') or out.get('price'))
        if not useful:
            # try microdata
            micro = _microdata_fallback_from_html(html)
            if micro and len(micro) > 1 and (micro.get('price') or micro.get('name')):
                out.update(micro)
                return out
            meta = _meta_fallback_from_html(html)
            if meta and (meta.get('price') or meta.get('title')):
                out.update(meta)
                return out
        return out
