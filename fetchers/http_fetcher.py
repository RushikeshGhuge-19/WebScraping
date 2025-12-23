"""Simple HTTP fetcher with optional proxy support.

This module provides a tiny wrapper over `requests.get` that reads
proxy configuration from environment variables and exposes a single
`fetch(url, timeout=30, headers=None) -> str` function returning the
response body as text.

Environment variables (optional):
- `PROXY_USER` - proxy username
- `PROXY_PASS` - proxy password (will be URL-encoded)
- `PROXY_HOST` - proxy host[:port], e.g. 'gb-pr.oxylabs.io:20000'

If `PROXY_HOST` is missing, no proxy is used.
"""
from __future__ import annotations

from typing import Optional, Dict
import os
from urllib.parse import quote

import requests

# Cache proxy configuration at module load to avoid repeated env lookups
_PROXY_HOST = os.environ.get('PROXY_HOST', '')
_PROXY_USER = os.environ.get('PROXY_USER', '')
_PROXY_PASS = os.environ.get('PROXY_PASS', '')
_CACHED_PROXIES: Optional[Dict[str, str]] = None


def _build_proxies() -> Optional[Dict[str, str]]:
    """Build proxy dict from cached environment variables."""
    global _CACHED_PROXIES
    if _CACHED_PROXIES is not None:
        return _CACHED_PROXIES if _CACHED_PROXIES else None
    
    if not _PROXY_HOST:
        _CACHED_PROXIES = {}
        return None

    auth = ''
    if _PROXY_USER:
        enc = quote(_PROXY_PASS, safe='')
        auth = f'{_PROXY_USER}:{enc}@'

    proxy_url = f'http://{auth}{_PROXY_HOST}'
    _CACHED_PROXIES = {'http': proxy_url, 'https': proxy_url}
    return _CACHED_PROXIES


def fetch(url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None) -> str:
    """Fetch `url` and return response text.

    Uses proxy settings from environment when available. Raises
    `requests.RequestException` for network errors so callers can decide
    how to handle retries/fallbacks.
    """
    resp = requests.get(
        url,
        headers=headers or {},
        timeout=timeout,
        proxies=_build_proxies(),
    )
    resp.raise_for_status()
    return resp.text


__all__ = ['fetch']
