"""Authoritative structural templates registry.

This module exports ONLY the finite set of structural templates used by
the scraping engine. Operational/parsing helpers such as JSON transport
or microdata extraction are NOT templates and should live in
`templates/*.py` as supporting modules.

STRUCTURAL TEMPLATES (exactly these 13) are grouped and aliased here so the engine imports a single canonical registry.
Listing templates (emit URLs only):
- listing_card
- listing_image_grid
- listing_ul_li
- listing_section
- listing_generic_anchor

Detail templates (emit car rows):
- detail_jsonld_vehicle
- detail_html_spec_table
- detail_hybrid_json_html
- detail_inline_html_blocks
- detail_image_gallery
Pagination templates (no rows):
- pagination_query
- pagination_path

Dealer info (site-level entity):
- dealer_info_jsonld
"""

from .listing_card import ListingCard
from .listing_image_grid import ListingImageGrid
from .section_listing import SectionListingTemplate as ListingSection
from .card_listing import CardListingTemplate
from .grid_listing import GridListingTemplate

from .detail_image_gallery import DetailImageGallery
from .detail_jsonld_vehicle import DetailJSONLDVehicle
from .detail_html_spec_table import DetailHTMLSpecTable
from .detail_hybrid_json_html import DetailHybridJSONHTML
from .detail_inline_html_blocks import DetailInlineHTMLBlocks

from .pagination_query import PaginationQueryTemplate
from .pagination_path import PaginationPathTemplate

from .dealer_info import DealerInfoTemplate as DealerInfoJSONLD


# To satisfy the canonical structural names we provide lightweight aliases
# (these inherit existing implementations; no new scraping logic is added).


class ListingULLI(GridListingTemplate):
    name = 'listing_ul_li'


class ListingGenericAnchor(CardListingTemplate):
    name = 'listing_generic_anchor'


# Authoritative detection order (detail first, then listings/pagination, then dealer)
ALL_TEMPLATES = [
    DetailHybridJSONHTML,
    DetailJSONLDVehicle,
    DetailInlineHTMLBlocks,
    DetailHTMLSpecTable,
    DetailImageGallery,
    ListingImageGrid,
    ListingCard,
    ListingULLI,
    ListingGenericAnchor,
    ListingSection,
    PaginationQueryTemplate,
    PaginationPathTemplate,
    DealerInfoJSONLD,
]


# Map by canonical template name -> class
TEMPLATE_BY_NAME = {cls.name: cls for cls in ALL_TEMPLATES}

__all__ = ["ALL_TEMPLATES", "TEMPLATE_BY_NAME"]
