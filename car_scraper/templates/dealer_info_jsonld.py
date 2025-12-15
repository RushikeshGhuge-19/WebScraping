"""Canonical wrapper: dealer_info_jsonld

Delegates to the existing site-level DealerInfoTemplate implementation
but exposes the canonical name required by the authoritative schema.
"""
from typing import Dict, Any
from .dealer_info import DealerInfoTemplate


class DealerInfoJSONLD(DealerInfoTemplate):
    name = 'dealer_info_jsonld'

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        return super().parse_car_page(html, car_url)
