"""Base template class for car scrapers.

Keep this file small — just the abstract API used by templates.
"""
from typing import List, Optional, Dict
from abc import ABC, abstractmethod

class CarTemplate(ABC):
    """Abstract base class for car page templates.

    Subclasses should implement `parse_car_page` and may override
    listing / pagination helpers when applicable.
    """
    name: str = "base"

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        """Return list of car listing URLs found on a listing page.

        Default implementation returns empty list.
        """
        return []

    def get_next_page(self, html: str, page_url: str) -> Optional[str]:
        """Return the next page URL or None if not found."""
        return None

    @abstractmethod
    def parse_car_page(self, html: str, car_url: str) -> Dict:
        """Parse a detail page and return a plain dict of extracted fields."""
        raise NotImplementedError()
