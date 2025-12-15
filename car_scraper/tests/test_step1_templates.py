"""Tests for the canonical-named templates from step 1."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from car_scraper.templates.detail_jsonld_vehicle import DetailJSONLDVehicle
from car_scraper.templates.detail_html_spec_table import DetailHTMLSpecTable
from car_scraper.templates.listing_card import ListingCard
from car_scraper.templates.listing_image_grid import ListingImageGrid


def test_detail_jsonld_vehicle():
    sample = Path(__file__).resolve().parent.parent / 'samples' / 'car_jsonld.html'
    html = sample.read_text(encoding='utf-8')
    tpl = DetailJSONLDVehicle()
    out = tpl.parse_car_page(html, str(sample))
    assert out.get('brand') == 'Fiat'
    assert out.get('model') == '500c'


def test_detail_html_spec_table():
    sample = Path(__file__).resolve().parent.parent / 'samples' / 'car_html_table.html'
    html = sample.read_text(encoding='utf-8')
    tpl = DetailHTMLSpecTable()
    out = tpl.parse_car_page(html, str(sample))
    specs = out.get('specs')
    assert specs.get('mileage') == '45,000 miles'


def test_listing_card_urls():
    sample = Path(__file__).resolve().parent.parent / 'samples' / 'listing_card.html'
    html = sample.read_text(encoding='utf-8')
    tpl = ListingCard()
    urls = tpl.get_listing_urls(html, 'https://example.com/list')
    assert any('car/10' in u for u in urls)


def test_listing_image_grid_urls():
    sample = Path(__file__).resolve().parent.parent / 'samples' / 'listing_grid.html'
    html = sample.read_text(encoding='utf-8')
    tpl = ListingImageGrid()
    urls = tpl.get_listing_urls(html, 'https://example.com/list')
    assert any('car/1' in u for u in urls)
