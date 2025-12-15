"""Simple test runner for HTML spec table template."""
from pathlib import Path
from pprint import pprint
from car_scraper.templates.html_spec_table import HTMLSpecTableTemplate


def main():
    sample = Path(__file__).resolve().parent.parent / 'samples' / 'car_html_table.html'
    html = sample.read_text(encoding='utf-8')
    tpl = HTMLSpecTableTemplate()
    out = tpl.parse_car_page(html, str(sample))
    pprint(out)


if __name__ == '__main__':
    main()
