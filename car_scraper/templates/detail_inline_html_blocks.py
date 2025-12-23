"""Detail template parsing inline label/value blocks and fallbacks.

This template extracts specs from common inline structures (dl/dt/dd,
label/value pairs, .label/.value, .spec-row) and also includes meta-tag
and microdata fallbacks when explicit structured data is missing.
"""
from __future__ import annotations

from typing import Dict, Any
import re
from bs4 import BeautifulSoup
from .base import CarTemplate
from .utils import finalize_detail_output
from ..utils.schema_normalizer import parse_mileage, parse_year, normalize_brand

# Pre-compiled regex for key normalization
_KEY_CLEAN_RE = re.compile(r'[^a-z0-9]+')


def _normalize_key(key: str) -> str:
    """Normalize spec key to lowercase alphanumeric with underscores."""
    return _KEY_CLEAN_RE.sub('_', key.lower()).strip('_')


class DetailInlineHTMLBlocks(CarTemplate):
    name = 'detail_inline_html_blocks'

    def _meta_fallback(self, soup: BeautifulSoup) -> Dict[str, Any]:
        out: Dict[str, Any] = {'_source': 'meta-fallback'}

        def meta(name: str = None, prop: str = None) -> str | None:
            if prop:
                tag = soup.find('meta', attrs={'property': prop})
                if tag and tag.get('content'):
                    return tag['content']
            if name:
                tag = soup.find('meta', attrs={'name': name})
                if tag and tag.get('content'):
                    return tag['content']
            return None

        out['title'] = meta(prop='og:title') or meta(name='title') or (soup.title.string if soup.title else None)
        out['price'] = meta(prop='product:price:amount') or meta(name='price')
        out['currency'] = meta(prop='product:price:currency') or meta(name='currency')
        out['description'] = meta(prop='og:description') or meta(name='description')
        return finalize_detail_output(out)

    def _microdata_fallback(self, soup: BeautifulSoup) -> Dict[str, Any]:
        out: Dict[str, Any] = {'_source': 'microdata-fallback'}
        for tag in soup.find_all(attrs={'itemscope': True}):
            it = (tag.get('itemtype') or '').lower()
            if 'vehicle' in it:
                for prop in ('name', 'brand', 'model', 'description', 'price'):
                    node = tag.find(attrs={'itemprop': prop})
                    if node:
                        out[prop] = node.get_text(strip=True)
                price_meta = tag.find('meta', attrs={'itemprop': 'price'})
                if price_meta and price_meta.get('content'):
                    out['price'] = price_meta['content']
                return finalize_detail_output(out)
        return finalize_detail_output(out)

    def _extract_mileage(self, val: str, out: Dict[str, Any]) -> None:
        """Extract mileage value and unit into output dict."""
        if 'mileage' not in out:
            out['mileage'] = val
            m_val, m_unit = parse_mileage(val)
            if m_val:
                out['mileage_value'] = m_val
                out['mileage_unit'] = m_unit

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, 'lxml')
        out: Dict[str, Any] = {'_source': 'inline-blocks', 'specs': {}}

        # Extract dl/dt/dd pairs
        dl = soup.find('dl')
        if dl:
            for dt in dl.find_all('dt'):
                dd = dt.find_next_sibling('dd')
                if not dd:
                    continue
                key = dt.get_text(separator=' ').strip()
                val = dd.get_text(separator=' ').strip()
                nk = _normalize_key(key)
                out['specs'][nk] = val
                key_lower = key.lower()
                if 'mileage' in key_lower:
                    self._extract_mileage(val, out)
                if 'fuel' in key_lower and 'fuel' not in out:
                    out['fuel'] = val
                if 'transmission' in key_lower and 'transmission' not in out:
                    out['transmission'] = val

        # label/value pairs (.label/.value or .spec-row)
        for label in soup.select('.label'):
            val = None
            nxt = label.find_next_sibling()
            if nxt and 'value' in (nxt.get('class') or []):
                val = nxt.get_text(strip=True)
            else:
                val_el = label.parent.select_one('.value')
                if val_el:
                    val = val_el.get_text(strip=True)
            if val:
                key = label.get_text(separator=' ').strip()
                nk = _normalize_key(key)
                out['specs'][nk] = val
                if 'mileage' in key.lower():
                    self._extract_mileage(val, out)

        # .spec-row style
        for row in soup.select('.spec-row'):
            lab = row.select_one('.spec') or row.select_one('th')
            valn = row.select_one('.value') or row.select_one('td')
            if lab and valn:
                key = lab.get_text(separator=' ').strip()
                val = valn.get_text(separator=' ').strip()
                nk = _normalize_key(key)
                out['specs'][nk] = val
                if 'mileage' in key.lower():
                    self._extract_mileage(val, out)

        # Fallbacks if no inline data found
        if not out['specs']:
            micro = self._microdata_fallback(soup)
            if micro and len(micro) > 1:
                out.update(micro)
                return finalize_detail_output(out)
            meta = self._meta_fallback(soup)
            if meta and (meta.get('price') or meta.get('title')):
                out.update(meta)
                return finalize_detail_output(out)

        # Normalize brand/year from specs
        specs = out.get('specs', {})
        if specs.get('brand') and not out.get('brand'):
            out['brand'] = normalize_brand(specs.get('brand'))
        if specs.get('year'):
            y = parse_year(specs.get('year'))
            if y:
                out['year'] = y

        return finalize_detail_output(out)
