"""Template package for car scrapers.

Only the authoritative template set is exported here. Extra standalone
templates (meta_tags, microdata_vehicle) were removed and their logic
is folded into the detail templates as fallbacks.
"""
from .base import CarTemplate

# Listing templates (do not emit rows)
from .listing_card import ListingCard
from .listing_image_grid import ListingImageGrid
from .section_listing import SectionListingTemplate as ListingSection

# Detail (car) templates (emit car rows)
from .detail_jsonld_vehicle import DetailJSONLDVehicle
from .detail_html_spec_table import DetailHTMLSpecTable
from .detail_hybrid_json_html import DetailHybridJSONHTML
from .detail_inline_html_blocks import DetailInlineHTMLBlocks

# Pagination templates (no rows)
from .pagination_query import PaginationQueryTemplate
from .pagination_path import PaginationPathTemplate

# Dealer info (site-level)
from .dealer_info_jsonld import DealerInfoJSONLD

__all__ = [
    "CarTemplate",
    # listings
    "ListingCard",
    "ListingImageGrid",
    "ListingSection",
    # details
    "DetailJSONLDVehicle",
    "DetailHTMLSpecTable",
    "DetailHybridJSONHTML",
    "DetailInlineHTMLBlocks",
    # pagination
    "PaginationQueryTemplate",
    "PaginationPathTemplate",
    # dealer
    "DealerInfoJSONLD",
]
