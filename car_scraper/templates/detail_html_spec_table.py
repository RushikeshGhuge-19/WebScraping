"""Canonical file `detail_html_spec_table.py` — delegates to existing html table implementation."""
from typing import Dict, Any
from .html_spec_table import HTMLSpecTableTemplate


class DetailHTMLSpecTable(HTMLSpecTableTemplate):
    name = 'detail_html_spec_table'

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        return super().parse_car_page(html, car_url)
