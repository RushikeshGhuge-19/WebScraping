from car_scraper.utils.schema_normalizer import SchemaNormalizer


def test_normalize_price_variants():
    cases = {
        "£4,995": 4995,
        "$12,345.00": 12345,
        "4995": 4995,
        5999: 5999,
        "": None,
    }
    for inp, exp in cases.items():
        out = SchemaNormalizer.normalize_price(inp)
        assert out == exp


def test_normalize_mileage_variants():
    cases = {
        "45,000 miles": 45000,
        "10000": 10000,
        "10 000 mi": 10000,
        None: None,
    }
    for inp, exp in cases.items():
        out = SchemaNormalizer.normalize_mileage(inp)
        assert out == exp


def test_normalize_year_and_brand():
    rec = {"year": "2015", "brand": "vw"}
    out, issues = SchemaNormalizer.normalize(rec)
    assert out["year"] == 2015
    assert out["brand"] == "Volkswagen"
    assert issues == []


def test_normalize_unparseable_fields():
    rec = {"price": "free", "mileage": "lots", "year": "nineteen ninety", "brand": ""}
    out, issues = SchemaNormalizer.normalize(rec)
    assert out["price"] is None
    assert out["mileage"] is None
    assert out["year"] is None
    assert out["brand"] is None
    assert set(issues) == {"price:unparsed", "mileage:unparsed", "year:unparsed", "brand:unparsed"}
