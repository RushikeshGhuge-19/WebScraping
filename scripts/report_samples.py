from car_scraper.engine import ScraperEngine
from pathlib import Path

def main():
    engine = ScraperEngine()
    res = engine.scrape_samples(Path('car_scraper/samples'))
    # pretty-print per-sample results
    print('\nPer-sample template detection and extracted fields:\n')
    template_counts = {}
    for r in res:
        sample = r.get('sample')
        tpl = r.get('template')
        car = r.get('car') or {}
        conf = car.get('confidence') if isinstance(car, dict) else None
        template_counts[tpl] = template_counts.get(tpl, 0) + 1
        print(f"Sample: {sample}")
        print(f"  Detected template: {tpl} (confidence={conf})")
        for k in ('name', 'brand', 'model', 'price', 'currency', 'mileage', 'year'):
            v = car.get(k) if car else None
            print(f"    {k}: {v}")
        print('')

    print('Template usage summary:')
    for tpl, cnt in sorted(template_counts.items(), key=lambda x: -x[1]):
        print(f"  {tpl}: {cnt}")

if __name__ == '__main__':
    main()
