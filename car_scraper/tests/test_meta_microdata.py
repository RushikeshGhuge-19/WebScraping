"""Tests for meta-tags and microdata templates."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from car_scraper.templates.meta_tags import MetaTagsTemplate
from car_scraper.templates.microdata_vehicle import MicrodataVehicleTemplate


def test_meta_tags():
    sample = Path(__file__).resolve().parent.parent / 'samples' / 'car_meta.html'
    html = sample.read_text(encoding='utf-8')
    tpl = MetaTagsTemplate()
    out = tpl.parse_car_page(html, str(sample))
    assert out.get('title') == '2017 Meta Car'
    assert out.get('price') == '7995'
    assert out.get('currency') == 'GBP'


def test_microdata():
    sample = Path(__file__).resolve().parent.parent / 'samples' / 'car_microdata.html'
    html = sample.read_text(encoding='utf-8')
    tpl = MicrodataVehicleTemplate()
    out = tpl.parse_car_page(html, str(sample))
    assert out.get('name') == '2016 Micro Car'
    assert out.get('brand') == 'MicroBrand'
    assert out.get('model') == 'M1'
    assert out.get('price') == '5995'
