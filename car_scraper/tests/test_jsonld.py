"""Simple test runner for JSON-LD Vehicle template."""
from pathlib import Path
from pprint import pprint
from car_scraper.templates.jsonld_vehicle import JSONLDVehicleTemplate


def main():
    sample = Path(__file__).resolve().parent.parent / 'samples' / 'car_jsonld.html'
    html = sample.read_text(encoding='utf-8')
    tpl = JSONLDVehicleTemplate()
    out = tpl.parse_car_page(html, str(sample))
    pprint(out)


if __name__ == '__main__':
    main()
