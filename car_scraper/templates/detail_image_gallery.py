"""Detail template to extract image galleries and video sources from vehicle pages.

Collects images from JSON-LD, Open Graph, gallery/carousel DOMs, and
`img` elements with `data-src`/`data-large` fallbacks. Returns a dict
with `images` and `videos` lists.
"""
from __future__ import annotations

from typing import Dict, Any, List
import json
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base import CarTemplate

_SCRIPT_JSONLD_RE = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)

# Gallery CSS selectors (combined for efficiency)
_GALLERY_SELECTORS = '.gallery, .carousel, .thumbnails, .slider, ul.gallery'

# Large image hint keywords
_LARGE_HINTS = frozenset(('large', 'full', 'zoom', '1024', '800'))


class DetailImageGallery(CarTemplate):
    name = 'detail_image_gallery'

    def _collect_from_jsonld(self, html: str, base: str) -> List[str]:
        out: List[str] = []
        for raw in _SCRIPT_JSONLD_RE.findall(html):
            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                img = item.get('image') or item.get('images')
                if isinstance(img, str):
                    out.append(urljoin(base, img))
                elif isinstance(img, list):
                    out.extend(urljoin(base, i) for i in img if isinstance(i, str))
        return out

    def _collect_from_dom(self, soup: BeautifulSoup, base: str) -> List[str]:
        out: List[str] = []

        # Common gallery selectors
        for container in soup.select(_GALLERY_SELECTORS):
            for img in container.find_all('img'):
                src = img.get('data-large') or img.get('data-src') or img.get('src') or img.get('data-original')
                if src:
                    out.append(urljoin(base, src))

        # Dragon2000 specific selectors
        for a in soup.select('div.vehicle-content-slider--side-thumbs__carousel a[href], div.vehicle-content-slider-container a[href]'):
            href = a.get('href')
            if href:
                out.append(urljoin(base, href))

        for img in soup.select('div.vehicle-content-slider--side-thumbs__thumbs-prev img[data-src]'):
            src = img.get('data-src')
            if src:
                out.append(urljoin(base, src))

        # Fallback: any img with large/zoom hints
        for img in soup.find_all('img'):
            src = img.get('data-large') or img.get('data-src') or img.get('src')
            if src:
                src_lower = src.lower()
                if any(h in src_lower for h in _LARGE_HINTS):
                    out.append(urljoin(base, src))

        # OG image
        og = soup.find('meta', attrs={'property': 'og:image'})
        if og:
            content = og.get('content')
            if content:
                out.append(urljoin(base, content))

        return out

    def _collect_videos(self, soup: BeautifulSoup, base: str) -> List[str]:
        vids: List[str] = []
        for video in soup.find_all('video'):
            src = video.get('src')
            if src:
                vids.append(urljoin(base, src))
            for src_tag in video.find_all('source'):
                s = src_tag.get('src')
                if s:
                    vids.append(urljoin(base, s))
        return vids

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, 'lxml')

        images = self._collect_from_jsonld(html, car_url)
        images.extend(self._collect_from_dom(soup, car_url))
        # Dedupe while preserving order
        images = list(dict.fromkeys(i for i in images if i))

        videos = list(dict.fromkeys(self._collect_videos(soup, car_url)))

        return {'_source': 'image-gallery', 'images': images, 'videos': videos}
