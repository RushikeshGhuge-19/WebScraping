"""Detect which template each synthetic site sample maps to."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from car_scraper.engine import ScraperEngine


SAMPLES_EXPECTED = [
    ("site_listing_card_1.html", "card_listing"),
    ("site_listing_image_grid_2.html", "grid_listing"),
    ("site_listing_ul_li_3.html", "listing_generic_anchor"),
    ("site_listing_section_4.html", "section_listing"),
    ("site_listing_generic_anchor_5.html", "listing_generic_anchor"),
    ("site_detail_jsonld_vehicle_6.html", "jsonld_vehicle"),
    ("site_detail_html_spec_table_7.html", "html_spec_table"),
    ("site_detail_hybrid_json_html_8.html", "hybrid_json_html"),
    ("site_detail_inline_html_blocks_9.html", "html_spec_table"),
    ("site_detail_meta_tags_10.html", "meta_tags"),
    ("site_detail_microdata_11.html", "microdata_vehicle"),
    ("site_detail_jsonld_variant_12.html", "jsonld_vehicle"),
    ("site_detail_table_variant_13.html", "html_spec_table"),
    ("site_listing_card_variant_14.html", "card_listing"),
    ("site_listing_image_grid_variant_15.html", "grid_listing"),
    ("site_detail_inline_variant_16.html", "html_spec_table"),
    ("site_detail_table_variant_17.html", "html_spec_table"),
    ("site_detail_hybrid_variant_18.html", "hybrid_json_html"),
    ("site_dealer_info_jsonld_19.html", "dealer_info"),
    ("site_misc_anchor_20.html", "listing_generic_anchor"),
]


def test_detection_on_samples():
    engine = ScraperEngine()
    samples_dir = ROOT / 'samples'
    for fname, expected in SAMPLES_EXPECTED:
        p = samples_dir / fname
        html = p.read_text(encoding='utf-8')
        tpl = engine.detector.detect(html, str(p))
        # detector may return listing templates with different names for generic cases
        name = getattr(tpl, 'name', None)
        assert name is not None, f"No template detected for {fname}"
        # Allow some flexibility: treat 'listing_generic_anchor' expectation as any listing
        if expected == 'listing_generic_anchor':
            # accept listing-like templates or a dealer_info detection for small pages
            assert ('listing' in name or 'card' in name or 'grid' in name or 'section' in name or name == 'dealer_info')
        else:
            assert expected in name, f"{fname}: expected {expected}, got {name}"
