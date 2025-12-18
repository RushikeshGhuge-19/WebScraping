Architecture and Template Classification
======================================

Purpose
-------
This document records the canonical template architecture and classification
policy for the scraping framework. It defines which modules are considered
STRUCTURAL TEMPLATES (a fixed, finite set) and which modules are supporting
parsing strategies, fallbacks, or transport helpers.

Why this matters
-----------------
Allowing arbitrary template files to be treated as first-class templates
leads to template explosion and brittle detection logic. We therefore
enforce a finite structural template surface and keep transport/parsing
strategies as re-usable helpers.

Canonical template classes (exactly 12)
--------------------------------------
The engine imports a single authoritative registry from
`car_scraper.templates.all_templates.ALL_TEMPLATES`. That list MUST contain
exactly the following structural templates. Do not add or remove entries
from this list without a deliberate architecture decision.

Listing templates (emit URLs only — never car data rows)
- `listing_card`
- `listing_image_grid`
- `listing_ul_li`
- `listing_section`
- `listing_generic_anchor`

Detail templates (emit car data rows — canonical normalized schema)
- `detail_jsonld_vehicle`
- `detail_html_spec_table`
- `detail_hybrid_json_html`
- `detail_inline_html_blocks`

Pagination templates (structural, no car rows)
- `pagination_query`
- `pagination_path`

Dealer info (site-level entity)
- `dealer_info_jsonld`

Supporting modules (NOT templates)
--------------------------------
The following categories are SUPPORTING modules and must not be included
in `ALL_TEMPLATES`:

- transport/parsing helpers: `json_api_listing`, `ajax_infinite_listing`
- data-format fallbacks: `microdata_vehicle`, `meta_tags`
- utility normalizers: `utils.py` (parse_price/parse_mileage/normalize_brand)

These modules should be invoked by structural templates when needed but
must not be registered as independent templates.

Canonical Detail output schema
------------------------------
All DETAIL templates must return a dict containing the following keys
explicitly (value None if unavailable):

- `brand`
- `model`
- `year`
- `price_value`  (numeric, float or None)
- `price_raw`    (original string or None)
- `currency`
- `mileage_value` (int or None)
- `mileage_unit`  (e.g., 'mi' or None)
- `fuel`
- `transmission`
- `description`
- `raw`          (raw representation of extracted structured data)

Separation of concerns
----------------------
- Structural templates: responsible for detecting page *structure* and
  emitting either URLs (LISTING) or a single car row (DETAIL) or pagination
  tokens (PAGINATION). They must not embed transport-specific logic.
- Supporting modules: responsible for parsing JSON blobs, extracting
  microdata/meta fallbacks, or normalizing values. They do not appear in
  the structural registry and are reusable across templates.

Enforcement
-----------
The repository includes a unit test `car_scraper/tests/test_template_classification.py`
which asserts that ONLY detail templates emit rows with the canonical keys,
and that listing/pagination templates do not return car rows. Maintain this
test whenever templates or classification change.

Maintainer guidance
-------------------
- When adding new parsing logic, add it as a supporting module and call it
  from the appropriate structural template.
- If you need a new structural template (rare), update `ARCHITECTURE.md` and
  obtain review from the architecture owners.

End of document.
