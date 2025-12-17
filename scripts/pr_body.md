Title: Improve templates: normalization, detector scoring, utils, and tooling

This PR contains a set of changes to improve parsing accuracy, maintainability, and developer tooling:

- Add `car_scraper/templates/utils.py` with shared helpers:
  - JSON-LD extraction, meta/microdata helpers
  - `parse_price`, `parse_mileage`, `parse_year`, `normalize_brand`
- Refactor JSON-LD and detail templates to use the utils and emit `confidence` and `_source`.
- Add scoring-based `TemplateDetector` in `car_scraper/engine.py` to reduce misclassification.
- Normalize price/mileage/year fields and add unit tests for utilities.
- Add `scripts/accuracy_runner.py` and a small `ground_truth.csv` example to compute baseline metrics.
- Add `scripts/setup_proxy_bs_selenium.py` showing proxy usage for `requests`, Chrome and Firefox Selenium drivers.
- Add tests: `tests/test_detector.py`, `tests/test_utils.py` and other small updates.

Why:
- Reduce duplication and centralize parsing logic.
- Provide a baseline accuracy harness for iterative improvements.
- Make it easier to run samples under proxies and with headless browsers for sites requiring JS.

Notes:
- The accuracy harness expects a `ground_truth.csv` (script includes an example).
- Selenium authenticated proxies can be tricky; the script documents options and includes a Firefox profile example. For robust proxy-auth with browsers consider `selenium-wire` or a local proxy forwarder.

Next steps (follow-up PRs):
- Implement `SchemaNormalizer` to coerce and validate canonical output.
- Expand accuracy harness and add CI reporting.
- Improve multi-site heuristics and add more labeled samples.
