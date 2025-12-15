"""Pytest tests for HTML spec table template."""
import sys
from pathlib import Path

# Ensure project root is on sys.path so `car_scraper` resolves when pytest
# is invoked from the repo root or when running the file directly.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from car_scraper.templates.html_spec_table import HTMLSpecTableTemplate


def test_parse_html_spec_table():
    sample_path = Path(__file__).resolve().parent.parent / 'samples' / 'car_html_table.html'
    html = sample_path.read_text(encoding='utf-8')
    tpl = HTMLSpecTableTemplate()
    out = tpl.parse_car_page(html, str(sample_path))

    specs = out.get('specs') or {}
    assert specs.get('mileage') == '45,000 miles'
    assert specs.get('engine_size') == '3.0 L'
    assert specs.get('fuel_type') == 'Diesel'
    assert specs.get('transmission') == 'Automatic'
