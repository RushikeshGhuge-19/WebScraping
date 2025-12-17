"""Canonical file `listing_card.py` — wrapper to standardize naming.

Delegates to CardListingTemplate to preserve a canonical template name
while avoiding duplication.
"""
from typing import List
from .card_listing import CardListingTemplate


class ListingCard(CardListingTemplate):
    """Canonical wrapper: card-based listings."""
    name = 'listing_card'
