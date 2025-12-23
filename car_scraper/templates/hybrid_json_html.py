"""Hybrid template: prefer JSON-LD for core fields, fallback to HTML specs.

This template attempts to parse price/model/name from JSON-LD Vehicle
objects and supplements missing fields by scraping spec tables from HTML.
"""
from __future__ import annotations

from typing import Dict, Any
import re
from bs4 import BeautifulSoup
from .base import CarTemplate
from .utils import (
    parse_mileage, parse_year, normalize_brand, parse_price,
    extract_jsonld_objects
)

# Pre-compiled regex for key normalization
_KEY_SPACE_RE = re.compile(r'\s+')


def _extract_text(node: Any) -> str | None:
    """Extract plain text from a node (string, dict, or nested)."""
    if node is None:
        return None
    if isinstance(node, str):
        return node.strip()
    if isinstance(node, dict):
        return node.get('name') or node.get('title')
    return str(node).strip()


def _is_vehicle(obj: Dict[str, Any]) -> bool:
    """Check if JSON-LD object is a Vehicle type."""
    t = obj.get('@type')
    return bool(t) and 'vehicle' in str(t).lower()


class HybridJSONHTMLTemplate(CarTemplate):
    name = 'hybrid_json_html'

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        out: Dict[str, Any] = {'_source': 'hybrid', 'specs': {}}

        # Try JSON-LD first
        for item in extract_jsonld_objects(html):
            if not isinstance(item, dict) or not _is_vehicle(item):
                continue

            out['name'] = _extract_text(item.get('name'))
            brand_raw = _extract_text(item.get('brand') or item.get('manufacturer'))
            out['brand'] = normalize_brand(brand_raw)
            out['model'] = _extract_text(item.get('model') or item.get('vehicleModel'))

            # Parse offer/price information
            offers = item.get('offers') or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            raw_price = _extract_text(offers.get('price') or item.get('price'))
            amt, cur = parse_price(raw_price)
            out['price_raw'] = raw_price
            out['price'] = raw_price
            out['price_value'] = amt
            out['currency'] = cur or _extract_text(offers.get('priceCurrency'))

            # Extract year from multiple possible fields
            year_candidate = item.get('vehicleModelYear') or item.get('year') or item.get('modelYear')
            if year_candidate:
                y = parse_year(str(year_candidate))
                if y:
                    out['year'] = y
            # Fallback: try extracting from name
            if not out.get('year') and out.get('name'):
                y2 = parse_year(out['name'])
                if y2:
                    out['year'] = y2

            out['_raw_jsonld'] = item
            break

        # Parse HTML specs to fill gaps
        soup = BeautifulSoup(html, 'lxml')
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                cells = tr.find_all(['th', 'td'])
                if len(cells) < 2:
                    continue
                key = cells[0].get_text(separator=' ').strip().lower()
                val = cells[1].get_text(separator=' ').strip()
                nk = _KEY_SPACE_RE.sub('_', key)
                out['specs'][nk] = val

                key_lower = key
                if 'mileage' in key_lower and 'mileage' not in out:
                    out['mileage'] = val
                    m_val, m_unit = parse_mileage(val)
                    if m_val:
                        out['mileage_value'] = m_val
                        out['mileage_unit'] = m_unit
                if 'fuel' in key_lower and 'fuel' not in out:
                    out['fuel'] = val
                if 'transmission' in key_lower and 'transmission' not in out:
                    out['transmission'] = val

        # Normalize brand/year if present in specs
        specs = out.get('specs', {})
        if specs.get('brand') and not out.get('brand'):
            out['brand'] = normalize_brand(specs['brand'])
        if specs.get('year') and not out.get('year'):
            y = parse_year(specs['year'])
            if y:
                out['year'] = y

        return out
