"""Template to parse JSON-LD Vehicle schema from saved HTML.

This implementation uses shared utilities for JSON-LD extraction and
returns a small confidence score and provenance information.
"""
from __future__ import annotations

from typing import Dict, Any
from .base import CarTemplate
from .utils import extract_jsonld_objects
from ..utils.schema_normalizer import parse_price, parse_year

# Vehicle type names (lowercase local names)
_VEHICLE_TYPES = frozenset(('vehicle', 'car', 'automobile'))

# Empty result for no-match case
_EMPTY_RESULT: Dict[str, Any] = {'_source': 'json-ld', '_raw': {}, 'confidence': 0.0}


def _extract_text(node: Any) -> str | None:
    if node is None:
        return None
    if isinstance(node, str):
        return node.strip()
    if isinstance(node, dict):
        return _extract_text(node.get('name') or node.get('@value'))
    return str(node).strip()


def _is_vehicle(node: Any) -> bool:
    """Accept both Vehicle and Car types; handle lists and IRIs."""
    if not isinstance(node, dict):
        return False
    t = node.get('@type')
    if not t:
        return False
    types = [str(x).lower() for x in (t if isinstance(t, list) else [t]) if isinstance(x, str)]
    for x in types:
        # Split IRIs to local name
        local = x.rsplit('/', 1)[-1].rsplit('#', 1)[-1]
        if local in _VEHICLE_TYPES:
            return True
    return False


class JSONLDVehicleTemplate(CarTemplate):
    name = 'jsonld_vehicle'

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        objs = extract_jsonld_objects(html)

        for item in objs:
            # If this script tag is a top-level graph, iterate inner nodes
            if isinstance(item, dict) and isinstance(item.get('@graph'), list):
                items = item['@graph']
            else:
                items = [item]

            for node in items:
                if not isinstance(node, dict) or not _is_vehicle(node):
                    continue

                brand = node.get('brand') or node.get('manufacturer') or node.get('make')
                offers = node.get('offers') or {}
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}

                raw_price = _extract_text(offers.get('price') or node.get('price'))
                amt, cur = parse_price(raw_price)
                name_val = _extract_text(node.get('name'))
                model_val = _extract_text(node.get('model') or node.get('vehicleModel'))
                brand_val = _extract_text(brand)

                # Confidence: proportion of core fields
                core = sum(1 for v in (brand_val, model_val) if v and str(v).strip())
                if amt is not None and isinstance(amt, (int, float)) and amt >= 0:
                    core += 1

                return {
                    '_source': 'json-ld',
                    '_raw': node,
                    'confidence': round(core / 3.0, 2),
                    'brand': brand_val,
                    'model': model_val,
                    'name': name_val,
                    'description': _extract_text(node.get('description')),
                    'price_raw': raw_price,
                    'price': amt,
                    'currency': cur or _extract_text(offers.get('priceCurrency')),
                    'year': parse_year(name_val),
                }

        return _EMPTY_RESULT.copy()