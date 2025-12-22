# Scrapy car templates

Lightweight template collection and parsers for scraping UK/EU car dealer sites.

This repository contains a small engine of HTML/JSON parsing templates used to
discover listings, parse vehicle detail pages, and extract dealer metadata.
# Car Scraper Templates

Lightweight, template-driven parsers for extracting vehicle detail data and
listing URLs from UK/EU car dealer pages. The project is intentionally
conservative: templates parse HTML and embedded JSON (JSON-LD / microdata)
without executing JavaScript by default. Optional headless rendering is
available for sites that require JS execution.

This repository is focused on reusable parsing templates (listing, detail,
pagination, dealer) and a small engine that detects the appropriate template
for a page and returns normalized vehicle/dealer output.

---

## Contents

- `car_scraper/templates/` — canonical templates (detail, listing, pagination, dealer)
- `car_scraper/utils/` — shared helpers and normalizers (`schema_normalizer`, JSON-LD helpers)
- `car_scraper/db/` — optional MongoDB scaffold (`mongo_store.py`)
- `car_scraper/samples/` — sample HTML fixtures used by runners and tests
- `scripts/` — convenience scripts to run templates and save results
- `requirements.txt` — runtime dependencies

---

## Key Features

- Template-first architecture: add or extend templates without changing the engine.
- Robust JSON-LD and microdata parsing with fallbacks to meta tags and HTML spec tables.
- Canonical normalization into keys: `brand`, `model`, `year`, `price_value`,
  `mileage_value`, `currency`, etc., via `car_scraper/templates/utils.finalize_detail_output`
- Optional Selenium-based renderer for dynamic pages (`car_scraper/utils/renderer.py`).

---

## Installation

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Notes:
- `requirements.txt` includes `selenium` and `webdriver-manager` for optional
  rendering. You only need those if you use the `--render` option in runners.

---

## Usage

- Run the sample template runner (fast, no JS):

```powershell
python scripts/run_all_templates.py
```

- Run with headless Chrome rendering (slower, executes JS):

```powershell
python scripts/run_all_templates.py --render
```

- Quick smoke test:

```powershell
python scripts/run_template_smoke.py
```

- Save parsed JSON to MongoDB (set `MONGO_URI`, `MONGO_DB`, `MONGO_COLLECTION`):

```powershell
$env:MONGO_URI = 'mongodb://localhost:27017'
python scripts/save_parsed_to_mongo.py
```

---

## Template Architecture

Templates implement a small API (one or more of):

- `get_listing_urls(html, page_url)` — return list of detail URLs found on a
  listing page.
- `get_next_page(html, page_url)` — return a next-page URL when available.
- `parse_car_page(html, page_url)` — for detail templates, return normalized
  dicts that include canonical keys.

The authoritative set of templates is registered in
[car_scraper/templates/all_templates.py](car_scraper/templates/all_templates.py).

Canonical template names include (non-exhaustive):

- Detail templates: `detail_hybrid_json_html`, `detail_jsonld_vehicle`,
  `detail_inline_html_blocks`, `detail_html_spec_table`, `detail_image_gallery`
- Listing templates: `listing_image_grid`, `listing_card`, `listing_ul_li`,
  `listing_generic_anchor`, `listing_section`, `json_api_listing`, `listing_ajax_infinite`
- Pagination: `pagination_query`, `pagination_path`
- Dealer: `dealer_info_jsonld`

Add new templates by creating a file under `car_scraper/templates/` and
registering it in `all_templates.py` (preserving detection order).

---

## Normalization

The project normalizes extracted fields into canonical keys using
`car_scraper/utils/schema_normalizer.py` and `car_scraper/templates/utils.finalize_detail_output`.
Normalized/expected keys include:

- `brand`, `model`, `year`
- `price_value`, `price_raw`, `currency`
- `mileage_value`, `mileage_unit`
- `fuel`, `transmission`, `description`, `raw`

Templates should populate logical source fields and then call
`finalize_detail_output()` to fill and normalize canonical fields.

---

## Selenium renderer (optional)

If a site requires JavaScript to expose listing links or JSON-LD, an
optional headless renderer is available at `car_scraper/utils/renderer.py`.
Enable it with `--render` on the sample runner. The renderer uses
`webdriver-manager` to install the matching ChromeDriver automatically.

Caveats:
- Starting a new headless browser per page is slow. For batch runs consider
  reusing a single persistent driver (not implemented by default).
- Ensure Chrome/Chromium is installed on the host runner when using the
  renderer (CI runners typically have them preinstalled).

---

## Testing

- Unit tests are in `car_scraper/tests/` and use `pytest`.
- Run tests with:

```powershell
python -m pytest -q
```

I added a small set of regression tests for Dragon2000 fallbacks in
`car_scraper/tests/test_dragon2000_fallbacks.py`.

---

## CI

The repository includes a GitHub Actions workflow at
`.github/workflows/ci.yml` that runs tests across Python 3.10–3.12 and
generates a coverage report. Update repository secrets with `CODECOV_TOKEN`
if you want automatic uploads to Codecov.

---

## Contributing

Contributions should follow the template-first philosophy:

1. Add focused templates or conservative fallbacks under `car_scraper/templates/`.
2. Add tests in `car_scraper/tests/` using fixtures from `car_scraper/samples/`.
3. Open a pull request explaining the change and why it preserves the
   existing architecture.

Please avoid changing the engine architecture unless absolutely necessary.

---

## Troubleshooting

- If tests fail due to encoding or HTML parsing, ensure `lxml` is installed.
- For Selenium issues, verify Chrome/Chromium is available and the
  `webdriver-manager` can download drivers (CI environments may block downloads).

---

## License

MIT-style. Add an explicit `LICENSE` file if you need a different license.
