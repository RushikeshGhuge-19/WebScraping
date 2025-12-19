from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional


_PRICE_RE = re.compile(r"[-€£$\u00A3,\s]+")
_MILEAGE_RE = re.compile(r"[,\s]+")


class SchemaNormalizer:
    """Normalize common vehicle fields into canonical types.

    Methods are intentionally conservative: they return None when a value
    cannot be confidently normalized.
    """

    BRAND_MAP = {
        "vw": "Volkswagen",
        "volkswagen": "Volkswagen",
        "mini": "MINI",
        "bmw": "BMW",
        "ford": "Ford",
        "toyota": "Toyota",
    }

    @classmethod
    def normalize_price(cls, value: Any) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return int(value)
        s = str(value).strip()
        if s == "":
            return None
        # Remove currency symbols, commas and spaces
        cleaned = _PRICE_RE.sub("", s)
        try:
            # some values like '4995.00' or '4,995' -> int
            if "." in cleaned:
                return int(float(cleaned))
            return int(cleaned)
        except Exception:
            return None

    @classmethod
    def normalize_mileage(cls, value: Any) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return int(value)
        s = str(value).lower()
        if s == "":
            return None
        # remove 'miles', 'mi', etc.
        s = re.sub(r"\b(miles|mile|mi)\b", "", s)
        cleaned = _MILEAGE_RE.sub("", s)
        try:
            return int(float(cleaned))
        except Exception:
            return None

    @classmethod
    def normalize_year(cls, value: Any) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, int):
            year = value
        else:
            s = str(value).strip()
            if not s:
                return None
            # extract 4-digit year
            m = re.search(r"(19\d{2}|20\d{2})", s)
            if not m:
                return None
            year = int(m.group(0))
        now = datetime.now().year
        if 1900 <= year <= now + 1:
            return year
        return None

    @classmethod
    def normalize_brand(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        s = str(value).strip()
        if not s:
            return None
        key = s.lower()
        key = re.sub(r"[^a-z0-9]", "", key)
        mapped = cls.BRAND_MAP.get(key)
        if mapped:
            return mapped
        # Title case as fallback
        return s.title()

    @classmethod
    def normalize(cls, record: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """Normalize fields on a record in-place and return (normalized, issues).

        Returns a tuple of normalized record and list of issue messages for fields
        that could not be confidently normalized.
        """
        issues: List[str] = []
        out = dict(record)

        price = cls.normalize_price(record.get("price"))
        if price is None and record.get("price") is not None:
            issues.append("price:unparsed")
        out["price"] = price

        mileage = cls.normalize_mileage(record.get("mileage"))
        if mileage is None and record.get("mileage") is not None:
            issues.append("mileage:unparsed")
        out["mileage"] = mileage

        year = cls.normalize_year(record.get("year"))
        if year is None and record.get("year") is not None:
            issues.append("year:unparsed")
        out["year"] = year

        brand = cls.normalize_brand(record.get("brand"))
        if brand is None and record.get("brand") is not None:
            issues.append("brand:unparsed")
        out["brand"] = brand

        return out, issues


# Convenience wrapper functions matching old templates/utils.py signatures
# These are deprecated wrappers; prefer using SchemaNormalizer directly

def parse_price(txt: Optional[str]):
    """Parse price string -> (amount: float|None, currency: str|None).
    
    Deprecated: Use SchemaNormalizer.normalize_price() instead.
    This wrapper maintains compatibility with legacy template code.
    """
    if not txt:
        return None, None
    amt = SchemaNormalizer.normalize_price(txt)
    # Try to extract currency from original string
    import re as _re
    cur = None
    if isinstance(txt, str):
        m_code = _re.search(r"\b(GBP|USD|EUR|AUD|CAD|JPY|CHF)\b", txt, _re.I)
        if m_code:
            cur = m_code.group(1).upper()
        elif txt.startswith('£'):
            cur = 'GBP'
        elif txt.startswith('$'):
            cur = 'USD'
        elif txt.startswith('€'):
            cur = 'EUR'
    return amt, cur


def parse_mileage(txt: Optional[str]):
    """Parse mileage string -> (value_in_miles: int|None, unit: str|None).
    
    Deprecated: Use SchemaNormalizer.normalize_mileage() instead.
    This wrapper maintains compatibility with legacy template code.
    """
    val = SchemaNormalizer.normalize_mileage(txt)
    return val, 'mi' if val is not None else None


def parse_year(txt: Optional[str]) -> Optional[int]:
    """Extract 4-digit year from text -> year: int|None.
    
    Deprecated: Use SchemaNormalizer.normalize_year() instead.
    This wrapper maintains compatibility with legacy template code.
    """
    return SchemaNormalizer.normalize_year(txt)


def normalize_brand(txt: Optional[str]) -> Optional[str]:
    """Normalize brand name with alias mapping.
    
    Deprecated: Use SchemaNormalizer.normalize_brand() instead.
    This wrapper maintains compatibility with legacy template code.
    """
    return SchemaNormalizer.normalize_brand(txt)


__all__ = ["SchemaNormalizer", "parse_price", "parse_mileage", "parse_year", "normalize_brand"]
