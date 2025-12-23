"""SUPPORTING MODULE — Microdata parsing strategy (NOT a structural template).

This module implements a microdata parsing strategy used as a fallback
by DETAIL templates. It is intentionally a helper and MUST NOT be
registered as a structural template. Structural templates should invoke
these helpers where appropriate.
"""
from __future__ import annotations

from typing import Dict, Any
import logging
from .base import CarTemplate
from .utils import make_soup
from ..utils.schema_normalizer import parse_price, parse_mileage, parse_year, normalize_brand

_logger = logging.getLogger(__name__)

# Pre-built empty result for no-match case
_EMPTY_RESULT: Dict[str, Any] = {
    '_source': 'microdata',
    '_raw': None,
    'confidence': 0.0,
    'name': None,
    'brand': None,
    'model': None,
    'description': None,
    'price_raw': None,
    'price': None,
    'currency': None,
    'mileage': None,
    'mileage_unit': None,
    'year': None,
}


def _extract_text(node: Any) -> str | None:
    if node is None:
        return None
    content = getattr(node, 'get', lambda k: None)('content')
    if content:
        return content
    try:
        return node.get_text(strip=True)
    except (AttributeError, TypeError, ValueError) as exc:
        _logger.debug("_extract_text fallback: %s", exc)
        return str(node).strip()


class MicrodataVehicleTemplate(CarTemplate):
    name = 'microdata_vehicle'

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        soup = make_soup(html)

        # Find first itemscope that looks like a vehicle
        tag = None
        for t in soup.find_all(attrs={'itemscope': True}):
            if 'vehicle' in (t.get('itemtype') or '').lower():
                tag = t
                break

        if not tag:
            return _EMPTY_RESULT.copy()

        # Extract core fields
        name = _extract_text(tag.find(attrs={'itemprop': 'name'}))
        brand_raw = _extract_text(tag.find(attrs={'itemprop': 'brand'}))
        model = _extract_text(tag.find(attrs={'itemprop': 'model'}))
        description = _extract_text(tag.find(attrs={'itemprop': 'description'}))

        # Price
        price_node = tag.find(attrs={'itemprop': 'price'}) or tag.find('meta', attrs={'itemprop': 'price'})
        price_raw = _extract_text(price_node)
        amt, cur = parse_price(price_raw)

        # Mileage
        mileage_node = tag.find(attrs={'itemprop': 'mileageFromOdometer'}) or tag.find(attrs={'itemprop': 'mileage'})
        mval, munit = parse_mileage(_extract_text(mileage_node))

        # Year
        year_node = tag.find(attrs={'itemprop': 'vehicleModelYear'}) or tag.find(attrs={'itemprop': 'year'})
        year = parse_year(_extract_text(year_node))

        # Confidence: proportion of core fields present
        core = sum(1 for v in (normalize_brand(brand_raw), model, amt) if v)

        return {
            '_source': 'microdata',
            '_raw': dict(tag.attrs),
            'confidence': round(core / 3.0, 2),
            'name': name,
            'brand': normalize_brand(brand_raw),
            'model': model,
            'description': description,
            'price_raw': price_raw,
            'price': amt,
            'currency': cur,
            'mileage': mval,
            'mileage_unit': munit,
            'year': year,
        }
