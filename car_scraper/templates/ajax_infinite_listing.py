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
from typing import List, Dict, Any, Optional
import json
import re
from .base import CarTemplate
from .utils import make_soup

# Maximum recursion depth for nested JSON traversal to prevent stack overflow
MAX_RECURSION_DEPTH = 50


class AjaxInfiniteListingTemplate(CarTemplate):
    name = 'ajax_infinite_listing'

    def _collect_json(self, html: str) -> List[Any]:
        soup = make_soup(html)
        blobs: List[Any] = []
        # script tags with JSON-like content
        for tag in soup.find_all('script'):
            t = (tag.get('type') or '').lower()
            raw = tag.string or ''
            if 'json' in t:
                try:
                    data = json.loads(raw)
                except Exception:
                    continue
                blobs.append(data)
            else:
                # try to find JSON arrays/objects in inline JS
                for m in re.finditer(r'\{[\s\S]*?\}|\[[\s\S]*?\]', raw):
                    piece = m.group(0)
                    try:
                        data = json.loads(piece)
                    except Exception:
                        continue
                    blobs.append(data)
        return blobs

    def _find_urls(self, obj: Any, depth: int = 0, max_depth: int = MAX_RECURSION_DEPTH) -> List[str]:
        # Stop recursion at max depth to prevent stack overflow
        if depth >= max_depth:
            return []
        
        out: List[str] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str) and (v.startswith('http') or v.startswith('/')) and ('/vehicle' in v or 'listing' in v or 'car' in v):
                    out.append(v)
                else:
                    out.extend(self._find_urls(v, depth + 1, max_depth))
        elif isinstance(obj, list):
            for it in obj:
                out.extend(self._find_urls(it, depth + 1, max_depth))
        return out

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        blobs = self._collect_json(html)
        urls: List[str] = []
        for b in blobs:
            # common patterns: top-level `listings` or `results` arrays
            if isinstance(b, dict):
                for key in ('listings', 'results', 'items', 'data'):
                    if key in b:
                        urls.extend(self._find_urls(b[key]))
                # fallback: scan whole object
                urls.extend(self._find_urls(b))
            else:
                urls.extend(self._find_urls(b))

        # dedupe
        seen = set()
        out: List[str] = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                out.append(u)
        return out

    def get_next_page(self, html: str, page_url: str) -> Optional[str]:
        blobs = self._collect_json(html)
        for b in blobs:
            if isinstance(b, dict):
                for key in ('next', 'nextPage', 'next_page', 'next_url', 'more'):
                    if key in b and isinstance(b[key], str):
                        return b[key]
                # sometimes pagination present in meta
                for meta_key in ('meta', 'pagination', 'page'):
                    meta = b.get(meta_key)
                    if isinstance(meta, dict):
                        next_url = meta.get('next')
                        if next_url:
                            return next_url
        return None


class ListingAjaxInfiniteTemplate(CarTemplate):
    """Template to detect AJAX / infinite-scroll listing endpoints and extract URLs.

    This template inspects the page for common load-more patterns and XHR
    endpoints embedded in inline scripts (e.g., fetch/axios URLs, data-load
    attributes). It returns candidate listing URLs discovered in the page.
    """
    from typing import List
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base import CarTemplate

_FETCH_RE = re.compile(r"fetch\(['\"](.*?)['\"]")
_AXIOS_RE = re.compile(r"axios\.(get|post)\(['\"](.*?)['\"]")
_XHR_URL_RE = re.compile(r"['\"](\/[^'\"]+?(?:listing|list|search|load|api|ajax)[^'\"]*)['\"]", re.I)


class ListingAjaxInfiniteTemplate(CarTemplate):
    name = 'listing_ajax_infinite'

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        soup = BeautifulSoup(html, 'lxml')
        urls = []

        # 1) Look for container with data-load-url or data-next
        for el in soup.find_all(attrs={}) :
            # scanning attributes cheaply
            attrs = getattr(el, 'attrs', {})
            for a_k, a_v in attrs.items():
                if isinstance(a_v, str) and any(tok in a_k.lower() for tok in ('data-load', 'data-next', 'data-url')):
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

        # 4) fallback: find load-more anchor links
        for a in soup.find_all('a', href=True):
            if any(tok in (a.get_text(' ') or '').lower() for tok in ('load', 'more', 'show more')) or any(tok in a['href'].lower() for tok in ('page=', '/page/', 'offset=')):
                urls.append(urljoin(page_url, a['href']))

        # dedupe and return
        return list(dict.fromkeys(urls))

    def get_next_page(self, html: str, page_url: str):
        # prefer first discovered candidate
        found = self.get_listing_urls(html, page_url)
        return found[0] if found else None

    def parse_car_page(self, html: str, car_url: str):
        raise NotImplementedError()
