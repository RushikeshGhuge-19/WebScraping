"""Template to parse simple HTML spec tables into normalized dicts.

This is intentionally minimal: it finds table rows with a <th> and <td>
and converts the heading into a normalized key (lowercase, underscores).
"""
from typing import Dict, Any
import re
from bs4 import BeautifulSoup
from .base import CarTemplate


def _normalize_key(k: str) -> str:
    """Normalize key: lowercase, alphanumeric + underscore, collapse underscores."""
    k = k.strip().lower()
    k = re.sub(r"[^a-z0-9]+", '_', k)
    k = re.sub(r'__+', '_', k)
    return k.strip('_')


class HTMLSpecTableTemplate(CarTemplate):
    name = 'html_spec_table'

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        """Parse the first spec table found and return normalized specs dict."""
        soup = BeautifulSoup(html, 'lxml')
        table = soup.find('table')
        if not table:
            return {'_source': 'html-table', 'specs': {}}
        
        specs = {}
        for tr in table.find_all('tr'):
            cells = tr.find_all(['th', 'td'])
            if len(cells) < 2:
                continue
            # First cell is key, second is value
            key = cells[0].get_text(strip=True)
            val = cells[1].get_text(strip=True)
            nk = _normalize_key(key)
            specs[nk] = val
        
        return {'_source': 'html-table', 'specs': specs}
