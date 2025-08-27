# summary.py
import os
import json
import sqlite3
from typing import Any, Dict, List, Optional

# optional: openai (install with `pip install openai`) if you want to use an LLM
try:
    import openai
    _HAS_OPENAI = True
except Exception:
    _HAS_OPENAI = False

DB_NAME = "shadowhunter.db"

def get_conn():
    return sqlite3.connect(DB_NAME)

# ----------------------
# Data gathering helpers
# ----------------------
def fetch_target(target_id: int) -> Dict[str, Any]:
    """Récupère la ligne targets pour target_id."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, created_at, nom, prenom, pseudo, email, numero, localisation, alias FROM targets WHERE id = ?", (target_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise ValueError(f"Target id={target_id} introuvable.")
    keys = ["id", "created_at", "nom", "prenom", "pseudo", "email", "numero", "localisation", "alias"]
    return dict(zip(keys, row))

def fetch_email_breaches(target_id: int) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, email, breach_name, breach_title, breach_date, breach_domain, raw_json, found_at FROM email_breaches WHERE target_id = ?", (target_id,))
    rows = cur.fetchall()
    conn.close()
    items = []
    for r in rows:
        items.append({
            "id": r[0],
            "email": r[1],
            "breach_name": r[2],
            "breach_title": r[3],
            "breach_date": r[4],
            "breach_domain": r[5],
            "raw_json": json.loads(r[6]) if r[6] else None,
            "found_at": r[7]
        })
    return items

def fetch_source_results(target_id: int) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, source, type, url, score, summary, raw_json, found_at FROM source_results WHERE target_id = ?", (target_id,))
    rows = cur.fetchall()
    conn.close()
    items = []
    for r in rows:
        try:
            raw = json.loads(r[6]) if r[6] else None
        except Exception:
            raw = r[6]
        items.append({
            "id": r[0],
            "source": r[1],
            "type": r[2],
            "url": r[3],
            "score": r[4],
            "summary": r[5],
            "raw": raw,
            "found_at": r[7]
        })
    return items

def fetch_phone_lookups(target_id: int) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, numero, e164, country, carrier, is_valid, is_possible, raw_json, found_at FROM phone_lookups WHERE target_id = ?", (target_id,))
    rows = cur.fetchall()
    conn.close()
    items = []
    for r in rows:
        try:
            raw = json.loads(r[7]) if r[7] else None
        except Exception:
            raw = r[7]
        items.append({
            "id": r[0],
            "numero": r[1],
            "e164": r[2],
            "country": r[3],
            "carrier": r[4],
            "is_valid": bool(r[5]) if r[5] is not None else None,
            "is_possible": bool(r[6]) if r[6] is not None else None,
            "raw": raw,
            "found_at": r[8]
        })
    return items

# ----------------------
# Assemble report
# ----------------------
def assemble_report_items(target_id: int) -> List[Dict[str, Any]]:
    """Rassemble toutes les infos concernant target_id en une liste d'items numérotés."""
    target = fetch_target(target_id)
    items: List[Dict[str, Any]] = []

    # item 1 = target basic
    items.append({
        "index": 1,
        "category": "target",
        "summary": f"Target basic info (id={target['id']})",
        "data": target
    })

    idx = 2

    # email breaches
    breaches = fetch_email_breaches(target_id)
    for b in breaches:
        items.append({
            "index": idx,
            "category": "email_breach",
            "summary": f"Email breach: {b.get('breach_name') or 'unknown'}",
            "data": b
        })
        idx += 1

    # source results
    sources = fetch_source_results(target_id)
    for s in sources:
        items.append({
            "index": idx,
            "category": "source_result",
            "summary": f"Source {s.get('source')} / {s.get('type')}",
            "data": s
        })
        idx += 1

    # phone lookups
    phones = fetch_phone_lookups(target_id)
    for p in phones:
        items.append({
            "index": idx,
            "category": "phone_lookup",
            "summary": f"Phone lookup: {p.get('numero')}",
            "data": p
        })
        idx += 1

    return items

# ----------------------
# Export helpers
# ----------------------
def export_json(items: List[Dict[str, Any]], filename: str) -> str:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"items": items}, f, ensure_ascii=False, indent=2)
    return filename

def export_txt(items: List[Dict[str, Any]], filename: str) -> str:
    lines = []
    for it in items:
        lines.append(f"{it['index']}. [{it['category']}] {it['summary']}")
        # pretty print the data as compact json for readability
        try:
            lines.append(json.dumps(it['data'], ensure_ascii=False, indent=2))
        except Exception:
            lines.append(str(it['data']))
        lines.append("")  # blank line
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return filename

# ----------------------
# LLM summarization
# ----------------------
def _call_llm(prompt: str, model: str = "gpt-4o-mini") -> str:
    """
    Appelle OpenAI si OPENAI_API_KEY est défini et openai lib est installée.
    Retourne le texte résumé.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not _HAS_OPENAI:
        raise RuntimeError("OpenAI non configuré ou package openai manquant. Set OPENAI_API_KEY and install openai.")

    openai.api_key = api_key

    # build chat messages
    messages = [
        {"role": "system", "content": "Tu es un assistant qui résume des rapports OSINT de façon concise, claire et structurée."},
        {"role": "user", "content": prompt}
    ]

    # use chat completion
    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=800
        )
        # extract text
        text = resp["choices"][0]["message"]["content"].strip()
        return text
    except Exception as e:
        raise RuntimeError(f"Erreur appel LLM: {e}")

def llm_summarize_items(items: List[Dict[str, Any]], model: str = "gpt-4o-mini") -> str:
    """
    Construit un prompt à partir des items et appelle le LLM pour obtenir un résumé.
    Limite la taille du prompt si trop grand (on fournit les items essentiels).
    """
    # Build a compact textual representation
    parts = []
    for it in items:
        # keep summary + compact JSON (no huge raw JSON)
        data = it.get("data", {})
        # remove potentially huge raw fields
        safe_data = {k: (v if k != "raw" else "[raw omitted]") for k, v in (data.items() if isinstance(data, dict) else [])}
        parts.append(f"{it['index']}. [{it['category']}] {it['summary']}\n{json.dumps(safe_data, ensure_ascii=False)}")

    prompt_body = (
        "Voici les éléments d'une enquête OSINT (numérotés). "
        "Fais :\n"
        "1) Un résumé court (3-5 phrases) des informations principales trouvées.\n"
        "2) Les éléments de preuve clés (liste par numéro d'item).\n"
        "3) Les points d'attention / risques (liste courte).\n"
        "4) Recommandations d'étapes suivantes (max 5).\n\n"
        "Données :\n\n" + "\n\n".join(parts)
    )

    # If prompt too large, truncate
    if len(prompt_body) > 60000:
        prompt_body = prompt_body[:59000] + "\n\n[TRUNCATED]"  # keep within token limits

    return _call_llm(prompt_body, model=model)

# ----------------------
# Fallback summarizer
# ----------------------
def local_summarize_items(items: List[Dict[str, Any]]) -> str:
    """
    Résumé simple si pas d'API LLM : extractive + counts
    """
    lines = []
    lines.append("Résumé (local) :")
    # Quick key facts from target
    target_item = next((it for it in items if it["category"] == "target"), None)
    if target_item:
        t = target_item["data"]
        lines.append(f"- Cible: {t.get('prenom') or ''} {t.get('nom') or ''} (pseudo: {t.get('pseudo') or 'N/A'})")
        lines.append(f"- Email: {t.get('email') or 'N/A'}, Téléphone: {t.get('numero') or 'N/A'}")
        lines.append(f"- Alias proposés: {t.get('alias') or 'N/A'}")
    # counts
    n_breaches = sum(1 for it in items if it["category"] == "email_breach")
    n_sources = sum(1 for it in items if it["category"] == "source_result")
    n_phones = sum(1 for it in items if it["category"] == "phone_lookup")
    lines.append(f"- Breaches email trouvés: {n_breaches}")
    lines.append(f"- Résultats web / sources: {n_sources}")
    lines.append(f"- Lookups téléphone: {n_phones}")

    # list top 3 source_result summaries
    srcs = [it for it in items if it["category"] == "source_result"]
    if srcs:
        lines.append("- Top sources (extraits) :")
        for s in srcs[:3]:
            summary = s.get("summary") or s["data"].get("summary") or ""
            lines.append(f"  {s['index']}. {s.get('source')} - {summary}")

    lines.append("\nRecommandations :")
    recs = [
        "Vérifier les breaches email listées et récupérer les preuves (liens/download).",
        "Faire une recherche reverse-image si photo disponible.",
        "Vérifier la cohérence localisation/date entre posts trouvés.",
        "Collecter plus de sources indépendantes avant conclusions."
    ]
    for r in recs:
        lines.append(f"- {r}")

    return "\n".join(lines)

# ----------------------
# Public entrypoint
# ----------------------
def summarize_target(target_id: int, out_dir: str = ".", send_to_llm: bool = True, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Rassemble toutes les infos d'un target_id, exporte JSON + TXT, envoie au LLM (optionnel) et retourne le résumé.
    Retourne: { "files": {"json": path, "txt": path}, "summary": <text>, "llm_used": bool }
    """
    items = assemble_report_items(target_id)

    base = os.path.join(out_dir, f"target_{target_id}")
    json_path = export_json(items, base + ".json")
    txt_path = export_txt(items, base + ".txt")

    summary_text = None
    llm_used = False

    if send_to_llm:
        try:
            # Build a concise text to send: use the TXT file content (already numbered)
            with open(txt_path, "r", encoding="utf-8") as f:
                txt_content = f.read()
            if not _HAS_OPENAI or not os.environ.get("OPENAI_API_KEY"):
                # no key or package: fall back
                summary_text = local_summarize_items(items)
            else:
                summary_text = llm_summarize_items(items, model=model)
                llm_used = True
        except Exception as e:
            # On any error, fallback to local summary and include the error note
            summary_text = local_summarize_items(items) + f"\n\n(Note: LLM error: {e})"
            llm_used = False
    else:
        summary_text = local_summarize_items(items)

    # Save the summary to file
    summary_file = base + ".summary.txt"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary_text)

    return {
        "files": {"json": json_path, "txt": txt_path, "summary": summary_file},
        "summary": summary_text,
        "llm_used": llm_used
    }

# ----------------------
# CLI quick-run
# ----------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Summary generator for a target")
    parser.add_argument("target_id", type=int, help="ID of target to summarize")
    parser.add_argument("--out", default=".", help="Output directory")
    parser.add_argument("--no-llm", action="store_true", help="Don't call remote LLM; use local summary")
    parser.add_argument("--model", default="gpt-4o-mini", help="LLM model to use (OpenAI)")
    args = parser.parse_args()

    res = summarize_target(args.target_id, out_dir=args.out, send_to_llm=not args.no_llm, model=args.model)
    print("Fichiers générés :", res["files"])
    print("\nRésumé :\n")
    print(res["summary"])
