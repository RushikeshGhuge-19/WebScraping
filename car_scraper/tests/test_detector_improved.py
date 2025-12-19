from pathlib import Path
from car_scraper.engine import TemplateRegistry, TemplateDetector


SAMPLES_DIR = Path(__file__).resolve().parent.parent / 'samples'


def _load_sample(name: str) -> str:
    p = SAMPLES_DIR / name
    return p.read_text(encoding='utf-8')


def test_detector_picks_for_microdata_sample():
    html = _load_sample('car_microdata.html')
    registry = TemplateRegistry()
    detector = TemplateDetector(registry)
    tpl = detector.detect(html, 'file://sample')
    assert tpl is not None

