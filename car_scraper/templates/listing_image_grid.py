"""Canonical file `listing_image_grid.py` — delegates to grid listing implementation."""
from __future__ import annotations

from typing import List
from .grid_listing import GridListingTemplate


class ListingImageGrid(GridListingTemplate):
    name = 'listing_image_grid'

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        return super().get_listing_urls(html, page_url)
