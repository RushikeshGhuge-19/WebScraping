"""Canonical wrapper: detail_hybrid_json_html.

Reuses the existing HybridJSONHTMLTemplate but exposes the canonical
name required by the authoritative template set.
"""
from typing import Dict, Any
from .hybrid_json_html import HybridJSONHTMLTemplate


class DetailHybridJSONHTML(HybridJSONHTMLTemplate):
    name = 'detail_hybrid_json_html'

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        return super().parse_car_page(html, car_url)
