"""Template to parse JSON-LD Vehicle schema from saved HTML.

This template looks for <script type="application/ld+json"> blocks,
parses JSON-LD, and returns the first object whose @type indicates
"Vehicle".
"""
from typing import Dict, Any, Optional
import json
import re
import html as _html
from .base import CarTemplate

_SCRIPT_RE = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)


def _extract_text(node: Any) -> Optional[str]:
    if node is None:
        return None
    if isinstance(node, str):
        return node.strip()
    # sometimes brand/model are objects with name
    if isinstance(node, dict):
        return _extract_text(node.get('name') or node.get('@value'))
    return str(node).strip()


def _is_vehicle(node: Any) -> bool:
    t = node.get('@type') if isinstance(node, dict) else None
    if not t:
        return False
    if isinstance(t, list):
        types = [str(x).lower() for x in t]
    else:
        types = [str(t).lower()]
    return any('vehicle' in x for x in types)


class JSONLDVehicleTemplate(CarTemplate):
    name = 'jsonld_vehicle'

    def parse_car_page(self, html: str, car_url: str) -> Dict:
        """Parse the provided HTML and extract Vehicle JSON-LD into a dict.

        Returns a dictionary with common fields: brand, model, price, currency,
        description, name, and `_raw` for the matched JSON-LD object.
        """
        matches = _SCRIPT_RE.findall(html)
        for raw in matches:
            try:
                data = json.loads(_html.unescape(raw))
            except Exception:
                continue
            # data can be a list or dict; normalize to list
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                if _is_vehicle(item):
                    out: Dict[str, Any] = {}
                    # brand/ make variations
                    brand = item.get('brand') or item.get('manufacturer') or item.get('make')
                    out['brand'] = _extract_text(brand)
                    out['model'] = _extract_text(item.get('model') or item.get('vehicleModel'))
                    # price may be under offers
                    offers = item.get('offers') or {}
                    if isinstance(offers, list):
                        offers = offers[0] if offers else {}
                    out['price'] = _extract_text(offers.get('price') or item.get('price'))
                    out['currency'] = _extract_text(offers.get('priceCurrency'))
                    out['name'] = _extract_text(item.get('name'))
                    out['description'] = _extract_text(item.get('description'))
                    out['_raw'] = item
                    out['_source'] = 'json-ld'
                    return out
        return {'_source': 'json-ld', '_raw': None}
