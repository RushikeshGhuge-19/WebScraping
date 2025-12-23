"""Base template class for car scrapers.

Keep this file small — just the abstract API used by templates.
"""
from __future__ import annotations

from typing import List, Dict, Any
from abc import ABC


class CarTemplate(ABC):
    """Abstract base class for car page templates.

    Subclasses should implement `parse_car_page` and may override
    listing / pagination helpers when applicable.
    """
    name: str = 'base'

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        """Return list of car listing URLs found on a listing page."""
        raise NotImplementedError()

    def get_next_page(self, html: str, page_url: str) -> str | None:
        """Return the next page URL or None if not found."""
        return None

    def parse_car_page(self, html: str, car_url: str) -> Dict[str, Any]:
        """Parse a detail page and return a plain dict of extracted fields."""
        raise NotImplementedError()
