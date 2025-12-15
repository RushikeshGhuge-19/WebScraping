"""Canonical file `listing_card.py` — delegates to card listing implementation."""
from typing import List
from urllib.parse import urljoin
from .card_listing import CardListingTemplate


class ListingCard(CardListingTemplate):
    name = 'listing_card'

    def get_listing_urls(self, html: str, page_url: str) -> List[str]:
        return super().get_listing_urls(html, page_url)
