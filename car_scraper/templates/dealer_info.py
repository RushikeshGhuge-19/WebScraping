"""Dealer/site-level info extractor.

Parses JSON-LD for Organization / AutomotiveBusiness to extract site
level metadata such as name, address, phone and email.
"""
from __future__ import annotations

from typing import Dict, Any
import json
import logging
import re
import html as _html
from bs4 import BeautifulSoup
from .base import CarTemplate

# Pre-compiled regex patterns
_SCRIPT_RE = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)
_D2K_VAR_RE = re.compile(r"var\s+d2k\s*=\s*({[\s\S]+?})\s*;", re.I)
_D2K_EMAIL_RE = re.compile(r"dealerDetails\s*:\s*{[\s\S]*?Email\s*:\s*['\"]([^'\"]+)['\"]", re.I)

_logger = logging.getLogger(__name__)


def _get_text(node: Any) -> str | None:
    if node is None:
        return None
    if isinstance(node, str):
        return node.strip()
    if isinstance(node, dict):
        return node.get('name') or node.get('telephone') or node.get('email')
    return str(node)


class DealerInfoTemplate(CarTemplate):
    name = 'dealer_info_jsonld'

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, 'lxml')
        html_str = str(soup)

        # Search JSON-LD for Organization or AutomotiveBusiness
        for raw in _SCRIPT_RE.findall(html_str):
            try:
                data = json.loads(_html.unescape(raw))
            except json.JSONDecodeError as exc:
                _logger.debug("Skipping invalid JSON-LD blob: %s", exc)
                continue

            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                t = str(item.get('@type', ''))
                if 'Organization' in t or 'AutomotiveBusiness' in t:
                    address = item.get('address') or {}
                    addr_str = ', '.join(filter(None, [
                        address.get('streetAddress'),
                        address.get('addressLocality'),
                        address.get('addressRegion'),
                        address.get('postalCode'),
                        address.get('addressCountry'),
                    ])) if isinstance(address, dict) else None
                    return {
                        'name': _get_text(item.get('name')),
                        'telephone': _get_text(item.get('telephone') or item.get('phone')),
                        'email': _get_text(item.get('email')),
                        'address': addr_str,
                        '_raw': item,
                    }

        # Fallback: common page-level contact selectors
        out: Dict[str, Any] = {'name': None, 'telephone': None, 'email': None}

        # Dragon2000 inline JS fallback
        js_match = _D2K_VAR_RE.search(html_str)
        if js_match:
            m = _D2K_EMAIL_RE.search(js_match.group(1))
            if m:
                out['email'] = m.group(1).strip()

        tel = soup.select_one('a[href^="tel:"]')
        if tel:
            out['telephone'] = tel.get_text(strip=True)

        mail = soup.select_one('a[href^="mailto:"]')
        if mail:
            out['email'] = mail.get_text(strip=True)

        h1 = soup.find('h1')
        if h1:
            out['name'] = h1.get_text(strip=True)

        return out
