"""Run the ScraperEngine over local samples and optionally save results.

Usage:
  python main.py --out results.csv
"""
import argparse
import csv
import json
from pathlib import Path
from pprint import pprint
from car_scraper.engine import ScraperEngine


def main():
    p = argparse.ArgumentParser(description='Run ScraperEngine on saved samples and save to CSV')
    p.add_argument('--samples', '-s', default='car_scraper/samples', help='Samples directory')
    p.add_argument('--out', '-o', default='results.csv', help='Output CSV filename')
    args = p.parse_args()

    engine = ScraperEngine()
    root = Path(__file__).resolve().parent
    samples = root / args.samples
    results = engine.scrape_samples(samples)

    # Print results (short debug)
    for r in results:
        pprint(r)

    # Prepare outputs: cars.csv and dealers.csv
    cars_path = root / 'cars.csv'
    dealers_path = root / 'dealers.csv'
    cars_path.parent.mkdir(parents=True, exist_ok=True)

    car_columns = [
        'sample', 'template', 'brand', 'model', 'year', 'price_num', 'currency',
        'mileage_num', 'fuel', 'transmission', 'description', 'raw'
    ]

    dealer_columns = [
        'site', 'template', 'name', 'telephone', 'email', 'address', 'raw'
    ]

    def _extract(parsed: dict, key: str):
        if not parsed:
            return ''
        # top-level
        if key in parsed and parsed.get(key) is not None:
            return parsed.get(key)
        # specs dict
        specs = parsed.get('specs') if isinstance(parsed.get('specs'), dict) else {}
        if key in specs:
            return specs.get(key)
        # common variants
        if key == 'mileage':
            return specs.get('mileage') or specs.get('miles') or ''
        if key == 'price':
            return parsed.get('price') or (specs.get('price') if isinstance(specs.get('price'), str) else '')
        return ''

    import re

    def _parse_int(s):
        if not s:
            return ''
        if isinstance(s, (int, float)):
            return int(s)
        # remove non-digit characters except commas and dots
        s2 = re.sub(r"[^0-9.,]", "", str(s))
        s2 = s2.replace(',', '')
        try:
            if '.' in s2:
                return int(float(s2))
            return int(s2)
        except Exception:
            return ''

    def _parse_year(s):
        if not s:
            return ''
        text = str(s)
        m = re.search(r'(19\d{2}|20\d{2})', text)
        return m.group(0) if m else ''

    # We'll write two CSVs: cars (one row per car, only detail templates)
    # and dealers (one row per site, deduplicated by name/telephone).
    import logging
    logging.basicConfig(level=logging.INFO)

    # track dealers seen to ensure one-row-per-site
    seen_dealers = {}

    with cars_path.open('w', encoding='utf-8', newline='') as fh_cars, dealers_path.open('w', encoding='utf-8', newline='') as fh_dealers:
        cars_writer = csv.DictWriter(fh_cars, fieldnames=car_columns)
        dealers_writer = csv.DictWriter(fh_dealers, fieldnames=dealer_columns)
        cars_writer.writeheader()
        dealers_writer.writeheader()

        for r in results:
            tpl = r.get('template')
            # Cars: only accept the canonical detail templates
            car = r.get('car')
            if car and tpl in ('detail_jsonld_vehicle', 'detail_html_spec_table', 'detail_hybrid_json_html', 'detail_inline_html_blocks'):
                # normalize numeric values
                price_val = _extract(car, 'price') or ''
                price_num = _parse_int(price_val)
                mileage_val = _extract(car, 'mileage') or ''
                mileage_num = _parse_int(mileage_val)
                row = {
                    'sample': r.get('sample'),
                    'template': tpl,
                    'brand': _extract(car, 'brand') or '',
                    'model': _extract(car, 'model') or '',
                    'year': _parse_year(_extract(car, 'year') or _extract(car, 'name') or ''),
                    'price_num': price_num,
                    'currency': _extract(car, 'currency') or '',
                    'mileage_num': mileage_num,
                    'fuel': _extract(car, 'fuel') or '',
                    'transmission': _extract(car, 'transmission') or '',
                    'description': _extract(car, 'description') or '',
                    'raw': json.dumps(car, ensure_ascii=False) if car else ''
                }
                cars_writer.writerow(row)
            else:
                # If a non-detail template produced parsed output, log a warning
                if car:
                    logging.warning('Template %s produced car-like output; skipping row for sample %s', tpl, r.get('sample'))

            # Dealer rows: only accept dealer_info_jsonld and dedupe per name/telephone
            dealer = r.get('dealer')
            if dealer and tpl == 'dealer_info_jsonld':
                key = (dealer.get('name') or '').strip() or r.get('sample')
                tel = (dealer.get('telephone') or '').strip()
                key2 = (key, tel)
                if key2 not in seen_dealers:
                    seen_dealers[key2] = dealer
                    dealers_writer.writerow({
                        'site': key,
                        'template': tpl,
                        'name': dealer.get('name') or '',
                        'telephone': dealer.get('telephone') or '',
                        'email': dealer.get('email') or '',
                        'address': dealer.get('address') or '',
                        'raw': json.dumps(dealer, ensure_ascii=False) if dealer else ''
                    })
            else:
                if dealer:
                    logging.warning('Template %s produced dealer-like output; skipping sample %s', tpl, r.get('sample'))

    print(f"Saved cars to: {cars_path}")
    print(f"Saved dealers to: {dealers_path}")


if __name__ == '__main__':
    main()
