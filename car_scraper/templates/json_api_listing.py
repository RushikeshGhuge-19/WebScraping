"""SUPPORTING MODULE — JSON API listing transport mechanism (NOT a structural template).

This module implements a transport/parsing strategy to extract listing
URLs from embedded JSON blobs or inline JSON used by SPAs. It should be
invoked from structural LISTING templates when necessary, not treated
as an independent structural template.
"""
from typing import List, Dict, Any, Optional
import json
import logging
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from .base import CarTemplate
from .utils import make_soup

LOGGER = logging.getLogger(__name__)

# Whitelist of path segments that indicate listing/vehicle URLs
LISTING_PATH_SEGMENTS = {'car', 'cars', 'listing', 'listings', 'vehicle', 'vehicles', 'stock', 'used'}
# Maximum number of leading path segments to inspect for a listing indicator
MAX_CHECK_SEGMENTS = 3
# Plausible resource token: numeric id or slug-like string (lowercase letters,
# numbers and hyphens, length >= 3)
SLUG_RE = re.compile(r'^[a-z0-9-]{3,}$')

CONFIG_PATH = Path(__file__).resolve().parents[1] / 'config' / 'heuristics.json'


def _load_heuristics() -> Dict[str, Any]:
    try:
        with CONFIG_PATH.open('r', encoding='utf-8') as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        LOGGER.debug('Invalid heuristics config %s: %s', CONFIG_PATH, exc, exc_info=True)
        return {}


_HEURISTICS = _load_heuristics()
ALLOWED_DOMAINS = set(
    domain.lower()
    for domain in _HEURISTICS.get('listing_url_allowlist', [])
    if isinstance(domain, str)
)
_env_domains = os.environ.get('LISTING_DOMAINS')
if _env_domains:
    ALLOWED_DOMAINS.update(
        domain.strip().lower()
        for domain in _env_domains.split(',')
        if domain.strip()
    )
if not ALLOWED_DOMAINS:
    ALLOWED_DOMAINS = {'example.com'}

JSON_BLOB_MAX_BYTES = int(_HEURISTICS.get('json_blob_max_bytes', 131072))


class JSONAPIListingTemplate(CarTemplate):
    name = 'json_api_listing'

    def _extract_json_blobs(self, html: str) -> List[Dict[str, Any]]:
        soup = make_soup(html)
        out: List[Dict[str, Any]] = []
        # common: <script type="application/json">...</script>
        for tag in soup.find_all('script', type=lambda t: t and 'json' in t):
            raw = tag.string or ''
            if len(raw) > JSON_BLOB_MAX_BYTES:
                LOGGER.debug("Skipping oversized JSON blob (%d bytes)", len(raw))
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                LOGGER.debug("Skipping corrupt JSON blob: %s", exc)
                continue
            if isinstance(data, dict):
                out.append(data)

        # also try application/ld+json (some sites put arrays/objects with listings)
        for tag in soup.find_all('script', type='application/ld+json'):
            raw = tag.string or ''
            if len(raw) > JSON_BLOB_MAX_BYTES:
                LOGGER.debug("Skipping oversized JSON-LD blob (%d bytes)", len(raw))
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                # try to extract JSON object inside assignment
                m = re.search(r'={1}\s*({[\s\S]+})', raw)
                if not m:
                    continue
                try:
                    data = json.loads(m.group(1))
                except json.JSONDecodeError as exc:
                    LOGGER.debug("Fallback JSON parse failed: %s", exc)
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
            path = (parsed.path or '').lower()
            # If absolute URL, require allowlist on domain
            if parsed.scheme in ('http', 'https') and parsed.netloc:
                domain = parsed.netloc.split(':', 1)[0].lower()
                if domain not in ALLOWED_DOMAINS:
                    return False

            # Split path on "/" and consider only the leading components
            segments = [s for s in path.split('/') if s]
            if not segments:
                return False

            # Only inspect the first N segments to avoid false positives
            inspect_segments = segments[:MAX_CHECK_SEGMENTS]

            for idx, seg in enumerate(inspect_segments):
                if seg in LISTING_PATH_SEGMENTS:
                    # require a following plausible resource token (e.g., id or slug)
                    # e.g. /cars/123 or /vehicle/ford-fiesta
                    if idx + 1 < len(segments):
                        token = segments[idx + 1]
                        if token.isdigit() or SLUG_RE.match(token):
                            return True
                    # if there is no following token within inspected range, reject
                    return False
            return False
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

    def _normalize_page_url(self, page_url: Optional[str]) -> str:
        if not page_url or not isinstance(page_url, str):
            return 'http://example.com'
        return page_url

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        blobs = self._extract_json_blobs(html)
        urls: List[str] = []
        base_url = self._normalize_page_url(page_url)
        for b in blobs:
            raw_urls = self._find_urls_in_obj(b)
            # Resolve relative URLs to absolute using page_url
            urls.extend([urljoin(base_url, u) for u in raw_urls])

        # de-duplicate while preserving order
        return list(dict.fromkeys(urls))

    def get_next_page(self, html: str, page_url: str) -> Optional[str]:
        # try to extract a `next` or `page` URL from JSON blobs
        blobs = self._extract_json_blobs(html)
        base_url = self._normalize_page_url(page_url)
        for b in blobs:
            if isinstance(b, dict):
                for key in ('next', 'nextPage', 'next_page', 'pagination'):
                    if key in b and isinstance(b[key], str):
                        return urljoin(base_url, b[key])
                # nested pagination
                pag = b.get('pagination') or b.get('meta') or b.get('page')
                if isinstance(pag, dict):
                    next_url = pag.get('next')
                    if isinstance(next_url, str):
                        return urljoin(base_url, next_url)
        return None

    def parse_car_page(self, html: str, car_url: str):
        raise NotImplementedError()
