"""Template to parse simple HTML spec tables into normalized dicts.

This is intentionally minimal: it finds table rows with a <th> and <td>
and converts the heading into a normalized key (lowercase, underscores).
"""
from __future__ import annotations

from typing import Dict, Any
import re
from bs4 import BeautifulSoup
from .base import CarTemplate

# Pre-compiled regex for key normalization
_KEY_CLEAN_RE = re.compile(r'[^a-z0-9]+')
_UNDERSCORE_RE = re.compile(r'__+')


def _normalize_key(k: str) -> str:
    """Normalize key: lowercase, alphanumeric + underscore, collapse underscores."""
    k = _KEY_CLEAN_RE.sub('_', k.strip().lower())
    k = _UNDERSCORE_RE.sub('_', k)
    return k.strip('_')


class HTMLSpecTableTemplate(CarTemplate):
    name = 'html_spec_table'

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        """Parse the first spec table found and return normalized specs dict."""
        soup = BeautifulSoup(html, 'lxml')
        table = soup.find('table')
        if not table:
            return {'_source': 'html-table', 'specs': {}}
        
        specs: Dict[str, str] = {}
        for tr in table.find_all('tr'):
            cells = tr.find_all(['th', 'td'], recursive=False)
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                val = cells[1].get_text(strip=True)
                nk = _normalize_key(key)
                if nk:
                    specs[nk] = val
        
        return {'_source': 'html-table', 'specs': specs}
