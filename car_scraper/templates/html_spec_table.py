"""Template to parse simple HTML spec tables into normalized dicts.

This is intentionally minimal: it finds table rows with a <th> and <td>
and converts the heading into a normalized key (lowercase, underscores).
"""
from typing import Dict, Any
import re
import html as _html
from .base import CarTemplate

_TABLE_RE = re.compile(r'<table[^>]*>(.*?)</table>', re.I | re.S)
_TR_RE = re.compile(r'<tr[^>]*>(.*?)</tr>', re.I | re.S)
_TH_RE = re.compile(r'<th[^>]*>(.*?)</th>', re.I | re.S)
_TD_RE = re.compile(r'<td[^>]*>(.*?)</td>', re.I | re.S)


def _strip_tags(text: str) -> str:
    text = _html.unescape(text or '')
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()


def _normalize_key(k: str) -> str:
    k = k.strip().lower()
    k = re.sub(r"[^a-z0-9]+", '_', k)
    k = re.sub(r'__+', '_', k)
    return k.strip('_')


class HTMLSpecTableTemplate(CarTemplate):
    name = 'html_spec_table'

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        """Parse the first spec table found and return normalized specs dict."""
        m = _TABLE_RE.search(html)
        if not m:
            return {'_source': 'html-table', 'specs': {}}
        table_html = m.group(1)
        specs = {}
        for tr in _TR_RE.findall(table_html):
            thm = _TH_RE.search(tr)
            tdm = _TD_RE.search(tr)
            if not thm or not tdm:
                # some tables use two <td>s (key/value)
                tds = _TD_RE.findall(tr)
                if len(tds) >= 2:
                    key = _strip_tags(tds[0])
                    val = _strip_tags(tds[1])
                else:
                    continue
            else:
                key = _strip_tags(thm.group(1))
                val = _strip_tags(tdm.group(1))
            nk = _normalize_key(key)
            specs[nk] = val
        return {'_source': 'html-table', 'specs': specs}
