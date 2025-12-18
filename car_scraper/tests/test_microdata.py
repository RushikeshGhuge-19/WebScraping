from car_scraper.templates.microdata_vehicle import MicrodataVehicleTemplate
from pathlib import Path


def load_sample(name: str) -> str:
    p = Path(__file__).parent.parent / 'samples' / name
    return p.read_text(encoding='utf-8')


def test_microdata_sample():
    html = load_sample('car_microdata.html')
    tpl = MicrodataVehicleTemplate()
    out = tpl.parse_car_page(html, 'http://example/')
    assert out['price'] == 5995 or out['price_raw'] in ('5995', '5995.0')
    assert out['brand'] is not None
    assert out['model'] == 'M1'
    assert out['_source'] == 'microdata'
