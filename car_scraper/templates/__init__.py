"""Template package for car scrapers."""
from .base import CarTemplate
from .jsonld_vehicle import JSONLDVehicleTemplate
from .html_spec_table import HTMLSpecTableTemplate

__all__ = [
    "CarTemplate",
    "JSONLDVehicleTemplate",
    "HTMLSpecTableTemplate",
]
