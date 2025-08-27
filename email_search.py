import os
import requests
import time
from typing import Optional
import db

# HIBP endpoint (breached account)
HIBP_URL = "https://haveibeenpwned.com/api/v3/breachedaccount/{}"
# NOTE: HIBP requires an API key (hibp-api-key header). Place it in env var HIBP_API_KEY.

def _get_hibp_api_key() -> Optional[str]:
    return os.environ.get("HIBP_API_KEY")

def _call_hibp(email: str, truncate_response=True):
    """
    Appelle l'API HIBP. Retourne la JSON list of breaches or raises.
    Attention: l'API peut renvoyer 404 si pas de breach et 200 avec liste sinon.
    """
    api_key = _get_hibp_api_key()
    if not api_key:
        return {"error": "no_api_key", "message": "Aucune clé HIBP fournie (HIBP_API_KEY)."}

    headers = {
        "hibp-api-key": api_key,
        "user-agent": "ShadowHunter/1.0",
        "accept": "application/json"
    }
    url = HIBP_URL.format(requests.utils.requote_uri(email))
    resp = requests.get(url, headers=headers, params={"truncateResponse": str(truncate_response).lower()})
    # Respecter la rate limit: HIBP demande 1 request per 1.5s (voir docs) -> backoff simple
    if resp.status_code == 429:
        # rate limited: read Retry-After header if présent
        retry = int(resp.headers.get("Retry-After", "2"))
        time.sleep(retry)
        return _call_hibp(email, truncate_response)
    if resp.status_code == 404:
        return []  # no breaches for this account
    resp.raise_for_status()
    return resp.json()

def search_email(email: str, target_id: Optional[int] = None, save: bool = True) -> dict:
    """
    Lance des recherches OSINT liées à un email.
    - HIBP (si clé)
    - placeholder pour d'autres recherches (pastebins, dorks...) à ajouter plus tard.

    Sauvegarde les résultats en DB si save=True.
    Retour: dict résumé avec clefs 'hibp' etc.
    """
    results = {"email": email, "hibp": None, "notes": []}

    # HIBP
    try:
        hibp_res = _call_hibp(email)
        if isinstance(hibp_res, dict) and hibp_res.get("error") == "no_api_key":
            results["notes"].append("HIBP API key non fournie; pas de requête HIBP.")
        else:
            # hibp_res is a list (possibly empty)
            results["hibp"] = hibp_res
            if save and hibp_res:
                for breach in hibp_res:
                    db.save_email_breach(target_id, email, breach)
                results["notes"].append(f"{len(hibp_res)} breach(es) sauvegardée(s).")
            elif save:
                results["notes"].append("Aucun breach trouvé (HIBP).")
    except requests.HTTPError as e:
        results["notes"].append(f"Erreur HTTP HIBP: {e}")
    except Exception as e:
        results["notes"].append(f"Erreur HIBP inattendue: {e}")

    # TODO: ajouter ici d'autres sources (pastebin scrapers, google dorks, leaks archives)
    # Exemple d'enregistrement générique dans source_results si tu veux tracer un événement :
    # db.save_source_result(target_id, "email_module", "check_done", "", 0.0, "hibp_checked", {"hibp_count": len(hibp_res) if hibp_res else 0})

    return results
