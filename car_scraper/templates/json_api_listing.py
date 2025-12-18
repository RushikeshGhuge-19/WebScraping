"""SUPPORTING MODULE — JSON API listing transport mechanism (NOT a structural template).

This module implements a transport/parsing strategy to extract listing
URLs from embedded JSON blobs or inline JSON used by SPAs. It should be
invoked from structural LISTING templates when necessary, not treated
as an independent structural template.
"""
from typing import List, Dict, Any, Optional
import json
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from .base import CarTemplate
from .utils import make_soup

# Whitelist of path segments that indicate listing/vehicle URLs
LISTING_PATH_SEGMENTS = {'car', 'cars', 'listing', 'listings', 'vehicle', 'vehicles', 'stock', 'used'}


class JSONAPIListingTemplate(CarTemplate):
    name = 'json_api_listing'

    def _extract_json_blobs(self, html: str) -> List[Dict[str, Any]]:
        soup = make_soup(html)
        out: List[Dict[str, Any]] = []
        # common: <script type="application/json">...</script>
        for tag in soup.find_all('script', type=lambda t: t and 'json' in t):
            raw = tag.string or ''
            try:
                data = json.loads(raw)
            except Exception:
                continue
            if isinstance(data, dict):
                out.append(data)

        # also try application/ld+json (some sites put arrays/objects with listings)
        for tag in soup.find_all('script', type='application/ld+json'):
            raw = tag.string or ''
            try:
                data = json.loads(raw)
            except Exception:
                # try to extract JSON object inside assignment
                m = re.search(r'={1}\s*({[\s\S]+})', raw)
                if not m:
                    continue
                try:
                    data = json.loads(m.group(1))
                except Exception:
                    continue
            if isinstance(data, dict):
                out.append(data)

        return out

    def _is_listing_url(self, url_str: str) -> bool:
        """Check if a URL string appears to be a listing or vehicle URL.
        
        Parses the URL and checks if the path contains a whitelisted segment
        (e.g., "car", "listing", "vehicle") as a whole path component
        (case-insensitive).
        """
        try:
            parsed = urlparse(url_str)
            path = parsed.path.lower()
            # Split path on "/" and check for whitelisted segments
            segments = [s for s in path.split('/') if s]  # filter empty segments
            return any(seg in LISTING_PATH_SEGMENTS for seg in segments)
        except Exception:
            return False

    def _find_urls_in_obj(self, obj: Any) -> List[str]:
        urls: List[str] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str):
                    # Check if string looks like a URL (protocol-relative, absolute, or path-absolute)
                    if v.startswith(('http://', 'https://', '//', '/')):
                        if self._is_listing_url(v):
                            urls.append(v)
                else:
                    # Recursively search non-string values
                    urls.extend(self._find_urls_in_obj(v))
        elif isinstance(obj, list):
            for it in obj:
                urls.extend(self._find_urls_in_obj(it))
        return urls

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        blobs = self._extract_json_blobs(html)
        urls: List[str] = []
        for b in blobs:
            raw_urls = self._find_urls_in_obj(b)
            # Resolve relative URLs to absolute using page_url
            urls.extend([urljoin(page_url, u) for u in raw_urls])

        # de-duplicate while preserving order
        return list(dict.fromkeys(urls))

    def get_next_page(self, html: str, page_url: str) -> Optional[str]:
        # try to extract a `next` or `page` URL from JSON blobs
        blobs = self._extract_json_blobs(html)
        for b in blobs:
            if isinstance(b, dict):
                for key in ('next', 'nextPage', 'next_page', 'pagination'):
                    if key in b and isinstance(b[key], str):
                        return urljoin(page_url, b[key])
                # nested pagination
                pag = b.get('pagination') or b.get('meta') or b.get('page')
                if isinstance(pag, dict):
                    next_url = pag.get('next')
                    if isinstance(next_url, str):
                        return urljoin(page_url, next_url)
        return None

    def parse_car_page(self, html: str, car_url: str):
        raise NotImplementedError()
