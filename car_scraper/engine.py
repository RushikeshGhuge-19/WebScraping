"""Template registry, detector, and simple scraping engine.

This minimal engine is intended for offline parsing of saved HTML files.
It detects the most appropriate template for a page and dispatches parsing.
"""
from typing import List, Optional, Tuple, Dict, Any, Type
from pathlib import Path
import logging
from bs4 import BeautifulSoup
from .templates.utils import make_soup, extract_jsonld_objects

from .templates.all_templates import ALL_TEMPLATES, TEMPLATE_BY_NAME

logger = logging.getLogger(__name__)

# Allowed JSON-LD @type names for vehicle objects (case-insensitive)
VEHICLE_TYPE_NAMES = {'vehicle', 'car', 'automobile', 'vehiclemodel'}


def _extract_jsonld_type_names(type_value: Any) -> List[str]:
    """Extract normalized type names from JSON-LD @type field.
    
    Handles:
    - String types and full IRIs (splits on / and # to get local name)
    - Lists of type strings or IRIs
    Returns lowercase local type names.
    """
    if isinstance(type_value, str):
        types = [type_value]
    elif isinstance(type_value, list):
        types = type_value
    else:
        return []
    
    result = []
    for t in types:
        if not isinstance(t, str):
            continue
        # Extract local type name from IRI (e.g., https://schema.org/Vehicle -> Vehicle)
        local_name = t.split('/')[-1].split('#')[-1]
        result.append(local_name.lower())
    return result


def _is_jsonld_vehicle(obj: Dict) -> bool:
    """Check if a JSON-LD object represents a vehicle type.
    
    Uses exact type matching against a whitelist to avoid false positives
    from substring matches or stringified arrays.
    """
    if not isinstance(obj, dict):
        return False
    type_value = obj.get('@type')
    if not type_value:
        return False
    type_names = _extract_jsonld_type_names(type_value)
    return any(t in VEHICLE_TYPE_NAMES for t in type_names)


class TemplateRegistry:
    """Holds available template classes in detection order."""

    def __init__(self):
        # detection order comes from the centralized ALL_TEMPLATES list
        self._order = list(ALL_TEMPLATES)

    def classes(self) -> List[Type]:
        return self._order


class TemplateDetector:
    """Simple heuristic detector that picks the best template for HTML."""

    DETAIL_TEMPLATES = {
        'detail_hybrid_json_html': 0,
        'detail_jsonld_vehicle': 0,
        'detail_inline_html_blocks': 0,
        'detail_html_spec_table': 0,
    }
    LISTING_TEMPLATES = {'listing_image_grid', 'listing_card', 'listing_section'}
    PAGINATION_TEMPLATES = {'pagination_query', 'pagination_path'}

    def __init__(self, registry: TemplateRegistry):
        self.registry = registry

    def detect(self, html: str, page_url: str):
        """Detect the most appropriate template using heuristic scoring."""
        # Parse HTML once for reuse
        soup = make_soup(html)
        jsonld_objs = extract_jsonld_objects(html)

        # Detect page features
        has_table = bool(soup.find('table'))
        has_specs = bool(
            has_table
            or soup.select('.spec-row')
            or soup.select('.spec')
            or soup.find('dl')
            or (soup.select('.label') and soup.select('.value'))
        )
        has_jsonld_vehicle = any(
            _is_jsonld_vehicle(o) for o in jsonld_objs
        )

        candidates = []

        # Score detail templates
        detail_scores = dict(self.DETAIL_TEMPLATES)
        if has_jsonld_vehicle and has_specs:
            detail_scores['detail_hybrid_json_html'] += 3
        if has_jsonld_vehicle:
            detail_scores['detail_jsonld_vehicle'] += 2
        if has_specs:
            detail_scores['detail_inline_html_blocks'] += 1
        if has_table:
            detail_scores['detail_html_spec_table'] += 1

        for name, score in detail_scores.items():
            cls = TEMPLATE_BY_NAME.get(name)
            if cls and score > 0:
                candidates.append((cls(), score))

        # Score listing templates by URL count
        for name in self.LISTING_TEMPLATES:
            cls = TEMPLATE_BY_NAME.get(name)
            if not cls:
                continue
            tpl = cls()
            try:
                urls = tpl.get_listing_urls(html, page_url)
                if urls:
                    candidates.append((tpl, len(urls)))
            except NotImplementedError:
                # Expected for templates that don't implement this method
                pass
            except Exception as e:
                # Log unexpected errors to aid debugging
                logger.exception(f"Error scoring {name}.get_listing_urls: {e}")

        # Score pagination templates (1 point if next page found)
        for name in self.PAGINATION_TEMPLATES:
            cls = TEMPLATE_BY_NAME.get(name)
            if not cls:
                continue
            tpl = cls()
            try:
                if tpl.get_next_page(html, page_url):
                    candidates.append((tpl, 1))
            except NotImplementedError:
                # Expected for templates that don't implement this method
                pass
            except Exception as e:
                # Log unexpected errors to aid debugging
                logger.exception(f"Error scoring {name}.get_next_page: {e}")

        # Score dealer template if Organization JSON-LD present
        dealer_cls = TEMPLATE_BY_NAME.get('dealer_info_jsonld')
        if dealer_cls:
            for o in jsonld_objs:
                if isinstance(o, dict) and any(
                    x in str(o.get('@type', ''))
                    for x in ('Organization', 'AutomotiveBusiness')
                ):
                    candidates.append((dealer_cls(), 2))
                    break

        if not candidates:
            return None

        # Return best candidate (max score, ties broken by registry order)
        max_score = max(score for _, score in candidates)
        best = [tpl for tpl, score in candidates if score == max_score]
        
        if len(best) == 1:
            return best[0]

        # Tie-breaker: pick first in authoritative order
        for cls in self.registry.classes():
            for b in best:
                if isinstance(b, cls):
                    return b

        return best[0]


class ScraperEngine:
    """Runs detection and parsing on saved HTML files.

    Example usage:
        engine = ScraperEngine()
        engine.scrape_samples(Path('car_scraper/samples'))
    """

    def __init__(self):
        self.registry = TemplateRegistry()
        self.detector = TemplateDetector(self.registry)

    def scrape_file(self, file_path: Path) -> Dict[str, Any]:
        """Detect template and return structured output dict with explicit
        keys: 'car' for car detail dicts, 'dealer' for dealer info dicts.

        Listing and pagination templates do not create rows; they may provide
        'listing_urls' for downstream crawlers but those are NOT emitted to
        CSV by the runner.
        """
        html = file_path.read_text(encoding='utf-8')
        tpl = self.detector.detect(html, str(file_path))
        result: Dict[str, Any] = {'sample': file_path.name, 'template': tpl.name}

        car = None
        dealer = None
        listing_urls = None

        # Allowed detail templates names (authoritative)
        detail_names = {
            'detail_jsonld_vehicle',
            'detail_html_spec_table',
            'detail_hybrid_json_html',
            'detail_inline_html_blocks',
        }

        # Listing templates (do not emit rows)
        listing_names = {'listing_card', 'listing_image_grid', 'listing_section'}

        # Pagination templates (no rows)
        pagination_names = {'pagination_query', 'pagination_path'}

        # Dealer template name
        dealer_name = 'dealer_info_jsonld'

        try:
            parsed = tpl.parse_car_page(html, str(file_path))
        except NotImplementedError:
            parsed = None

        # If this template is a detail template, treat parsed as car
        if tpl.name in detail_names:
            car = parsed
        elif tpl.name == dealer_name:
            dealer = parsed
        elif tpl.name in listing_names:
            # try to extract listing URLs but do not produce car rows here
            try:
                listing_urls = tpl.get_listing_urls(html, str(file_path))
            except Exception:
                listing_urls = None
        elif tpl.name in pagination_names:
            # pagination: no rows
            pass
        else:
            # Unknown/unsupported template: do not let it emit car rows.
            # If it returned parsed data, keep it for debugging but do not
            # treat as car/dealer emission.
            if parsed:
                result['parsed_debug'] = parsed

        result['car'] = car
        result['dealer'] = dealer
        if listing_urls:
            result['listing_urls'] = listing_urls
        return result

    def scrape_samples(self, samples_dir: Path) -> List[Dict[str, Any]]:
        out = []
        for p in sorted(samples_dir.glob('*.html')):
            out.append(self.scrape_file(p))
        return out
