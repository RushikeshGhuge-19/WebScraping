"""SUPPORTING MODULE — AJAX/infinite listing helpers (NOT a structural template).

This module contains two related concerns:
 - low-level JSON extraction helpers (`AjaxInfiniteListingTemplate`) that
     are a transport/parsing strategy for XHR-injected listing data, and
 - a heuristics-based listing URL extractor (`ListingAjaxInfiniteTemplate`)
     that looks for fetch/axios/XHR endpoints and load-more anchors.

Both pieces are SUPPORTING code and MUST NOT be registered as structural
templates in `all_templates.py`. Structural listing templates should call
into these helpers where appropriate.
"""
from __future__ import annotations

from typing import List, Dict, Any
import json
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base import CarTemplate
from .utils import make_soup

# Maximum recursion depth for nested JSON traversal
_MAX_RECURSION_DEPTH = 50

# Pre-compiled regex patterns
_JSON_BLOB_RE = re.compile(r'\{[\s\S]*?\}|\[[\s\S]*?\]')
_FETCH_RE = re.compile(r"fetch\(['\"]([^'\"]+)['\"]")
_AXIOS_RE = re.compile(r"axios\.(get|post)\(['\"]([^'\"]+)['\"]")
_XHR_URL_RE = re.compile(r"['\"](\/[^'\"]+?(?:listing|list|search|load|api|ajax)[^'\"]*)['\"]", re.I)

# Keywords for URL detection
_URL_KEYWORDS = frozenset(('/vehicle', 'listing', 'car'))
_DATA_ATTR_KEYWORDS = frozenset(('data-load', 'data-next', 'data-url'))
_LOAD_MORE_KEYWORDS = frozenset(('load', 'more', 'show more'))
_PAGINATION_KEYWORDS = frozenset(('page=', '/page/', 'offset='))


class AjaxInfiniteListingTemplate(CarTemplate):
    name = 'ajax_infinite_listing'

    def _collect_json(self, html: str) -> List[Any]:
        soup = make_soup(html)
        blobs: List[Any] = []

        for tag in soup.find_all('script'):
            t = (tag.get('type') or '').lower()
            raw = tag.string or ''
            if 'json' in t:
                try:
                    data = json.loads(raw)
                    blobs.append(data)
                except (json.JSONDecodeError, ValueError):
                    pass
            else:
                # Try to find JSON arrays/objects in inline JS
                for m in _JSON_BLOB_RE.finditer(raw):
                    try:
                        data = json.loads(m.group(0))
                        blobs.append(data)
                    except (json.JSONDecodeError, ValueError):
                        pass
        return blobs

    def _find_urls(self, obj: Any, depth: int = 0) -> List[str]:
        if depth >= _MAX_RECURSION_DEPTH:
            return []

        out: List[str] = []
        if isinstance(obj, dict):
            for v in obj.values():
                if isinstance(v, str) and (v.startswith('http') or v.startswith('/')):
                    if any(kw in v for kw in _URL_KEYWORDS):
                        out.append(v)
                else:
                    out.extend(self._find_urls(v, depth + 1))
        elif isinstance(obj, list):
            for it in obj:
                out.extend(self._find_urls(it, depth + 1))
        return out

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        blobs = self._collect_json(html)
        urls: List[str] = []

        for b in blobs:
            if isinstance(b, dict):
                for key in ('listings', 'results', 'items', 'data'):
                    if key in b:
                        urls.extend(self._find_urls(b[key]))
                urls.extend(self._find_urls(b))
            else:
                urls.extend(self._find_urls(b))

        return list(dict.fromkeys(urls))

    def get_next_page(self, html: str, page_url: str) -> str | None:
        blobs = self._collect_json(html)
        for b in blobs:
            if isinstance(b, dict):
                for key in ('next', 'nextPage', 'next_page', 'next_url', 'more'):
                    if key in b and isinstance(b[key], str):
                        return b[key]
                for meta_key in ('meta', 'pagination', 'page'):
                    meta = b.get(meta_key)
                    if isinstance(meta, dict):
                        next_url = meta.get('next')
                        if next_url:
                            return next_url
        return None

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        raise NotImplementedError()


class ListingAjaxInfiniteTemplate(CarTemplate):
    """Template to detect AJAX / infinite-scroll listing endpoints and extract URLs."""
    name = 'listing_ajax_infinite'

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        soup = BeautifulSoup(html, 'lxml')
        urls: List[str] = []

        # 1) Look for container with data-load-url or data-next
        for el in soup.find_all(attrs=True):
            attrs = el.attrs
            for a_k, a_v in attrs.items():
                if isinstance(a_v, str) and any(tok in a_k.lower() for tok in _DATA_ATTR_KEYWORDS):
                    if a_v:
                        urls.append(urljoin(page_url, a_v))

        # 2) Find fetch/axios endpoints in scripts
        for m in _FETCH_RE.findall(html):
            urls.append(urljoin(page_url, m))
        for _g, m in _AXIOS_RE.findall(html):
            urls.append(urljoin(page_url, m))

        # 3) Heuristic XHR url matches inside scripts
        for m in _XHR_URL_RE.findall(html):
            urls.append(urljoin(page_url, m))

        # 4) Fallback: find load-more anchor links
        for a in soup.find_all('a', href=True):
            text = (a.get_text(' ') or '').lower()
            href = a['href'].lower()
            if any(tok in text for tok in _LOAD_MORE_KEYWORDS) or any(tok in href for tok in _PAGINATION_KEYWORDS):
                urls.append(urljoin(page_url, a['href']))

        return list(dict.fromkeys(urls))

    def get_next_page(self, html: str, page_url: str) -> str | None:
        found = self.get_listing_urls(html, page_url)
        return found[0] if found else None

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        raise NotImplementedError()
