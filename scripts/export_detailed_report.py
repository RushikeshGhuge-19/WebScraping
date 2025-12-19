import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARS_PATH = ROOT / 'cars.csv'
DEALERS_PATH = ROOT / 'dealers.csv'
OUTPUT = ROOT / 'full_scrape_report.csv'

FIELDS = [
    'scrape_type',
    'sample',
    'template',
    'brand',
    'model',
    'year',
    'price_num',
    'currency',
    'mileage_num',
    'fuel',
    'transmission',
    'description',
    'raw',
    'notes',
]

with OUTPUT.open('w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=FIELDS)
    writer.writeheader()

    if CARS_PATH.exists():
        with CARS_PATH.open('r', encoding='utf-8', newline='') as cars_fh:
            reader = csv.DictReader(cars_fh)
            for row in reader:
                notes = []
                if not row['brand'] and not row['model'] and not row['price_num']:
                    notes.append('no detail data parsed')
                if row['template'] not in ('detail_jsonld_vehicle', 'detail_hybrid_json_html', 'detail_inline_html_blocks', 'detail_html_spec_table'):
                    notes.append('non-detail template flagged')
                writer.writerow({
                    'scrape_type': 'car',
                    'sample': row['sample'],
                    'template': row['template'],
                    'brand': row['brand'],
                    'model': row['model'],
                    'year': row['year'],
                    'price_num': row['price_num'],
                    'currency': row['currency'],
                    'mileage_num': row.get('mileage_num', ''),
                    'fuel': row['fuel'],
                    'transmission': row['transmission'],
                    'description': row['description'],
                    'raw': row['raw'],
                    'notes': '; '.join(notes) if notes else 'parsed'
                })

    if DEALERS_PATH.exists():
        with DEALERS_PATH.open('r', encoding='utf-8', newline='') as dealers_fh:
            reader = csv.DictReader(dealers_fh)
            for row in reader:
                writer.writerow({
                    'scrape_type': 'dealer',
                    'sample': row['site'] or 'unknown',
                    'template': row['template'],
                    'brand': row['name'],
                    'model': '',
                    'year': '',
                    'price_num': '',
                    'currency': '',
                    'mileage_num': '',
                    'fuel': '',
                    'transmission': '',
                    'description': row['address'] or '',
                    'raw': row['raw'],
                    'notes': 'dealer info'
                })

print('Wrote', OUTPUT)
