# telephone_search.py
import json
from typing import Dict, Any, Optional

# dépendance optionnelle, installe via: pip install phonenumbers
try:
    import phonenumbers
    from phonenumbers import geocoder, carrier, NumberParseException
    _HAS_PHONENUM = True
except Exception:
    _HAS_PHONENUM = False

import db

def quick_phone_info(raw: str, default_region: str = "SN") -> Dict[str, Any]:
    """Retourne dict: e164, country, carrier, is_valid, is_possible, raw."""
    if not raw:
        return {"error": "empty_number", "raw": raw}

    if not _HAS_PHONENUM:
        # fallback simple si phonenumbers non installé
        digits = "".join(ch for ch in raw if ch.isdigit() or ch == "+")
        return {
            "raw": raw,
            "e164": digits if digits else None,
            "is_valid": None,
            "is_possible": None,
            "country": None,
            "carrier": None
        }

    try:
        pn = phonenumbers.parse(raw, default_region)
    except NumberParseException as e:
        return {"error": "parse_error", "message": str(e), "raw": raw}

    info = {
        "raw": raw,
        "e164": phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164) if phonenumbers.is_valid_number(pn) else None,
        "is_valid": phonenumbers.is_valid_number(pn),
        "is_possible": phonenumbers.is_possible_number(pn),
        "country": None,
        "carrier": None
    }

    try:
        info["country"] = geocoder.description_for_number(pn, "en")
    except Exception:
        info["country"] = None
    try:
        info["carrier"] = carrier.name_for_number(pn, "en")
    except Exception:
        info["carrier"] = None

    return info

def search_phone_and_save(numero: str, target_id: Optional[int] = None, save: bool = True) -> Dict[str, Any]:
    """
    Récupère les infos locales via quick_phone_info et enregistre en DB via db.save_phone_lookup.
    Retourne un dict avec le résumé.
    """
    result = quick_phone_info(numero)
    raw_json = json.dumps(result, ensure_ascii=False)

    if save:
        try:
            db.save_phone_lookup(
                target_id,
                numero,
                result.get("e164"),
                result.get("country"),
                result.get("carrier"),
                result.get("is_valid"),
                result.get("is_possible"),
                raw_json
            )
        except Exception as e:
            return {"ok": False, "error": f"DB save error: {e}", "result": result}

    return {"ok": True, "result": result}
