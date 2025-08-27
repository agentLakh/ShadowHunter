import sqlite3
import json
from typing import Optional

DB_NAME = "shadowhunter.db"

def get_conn():
    return sqlite3.connect(DB_NAME)

def init_db():
    """Crée les tables nécessaires si elles n'existent pas."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS targets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        nom TEXT,
        prenom TEXT,
        pseudo TEXT,
        email TEXT,
        numero TEXT,
        localisation TEXT,
        alias TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS email_breaches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_id INTEGER,
        email TEXT,
        breach_name TEXT,
        breach_title TEXT,
        breach_date TEXT,
        breach_domain TEXT,
        raw_json TEXT,
        found_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(target_id) REFERENCES targets(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS source_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_id INTEGER,
        source TEXT,
        type TEXT,
        url TEXT,
        score REAL,
        summary TEXT,
        raw_json TEXT,
        found_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(target_id) REFERENCES targets(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS phone_lookups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_id INTEGER,
        numero TEXT,
        e164 TEXT,
        country TEXT,
        carrier TEXT,
        is_valid INTEGER,
        is_possible INTEGER,
        raw_json TEXT,
        found_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(target_id) REFERENCES targets(id)
    )
    """)


    conn.commit()
    conn.close()

def save_target(data: dict) -> int:
    """
    Insère une cible dans targets. Retourne target_id.
    data: dict avec clés (nom, prenom, pseudo, email, numero, localisation, alias)
    """
    conn = get_conn()
    cur = conn.cursor()
    keys = []
    vals = []
    for k in ("nom", "prenom", "pseudo", "email", "numero", "localisation", "alias"):
        keys.append(k)
        vals.append(data.get(k))
    q_keys = ", ".join(keys)
    placeholders = ", ".join(["?"] * len(vals))
    cur.execute(f"INSERT INTO targets ({q_keys}) VALUES ({placeholders})", vals)
    target_id = cur.lastrowid
    conn.commit()
    conn.close()
    return target_id

def save_email_breach(target_id: Optional[int], email: str, breach: dict):
    """
    Sauvegarde une entrée breach (format HIBP) dans email_breaches.
    breach: dict contenant au moins 'Name', 'Title', 'BreachDate', 'Domain' ou raw JSON.
    """
    conn = get_conn()
    cur = conn.cursor()
    raw = json.dumps(breach, ensure_ascii=False)
    breach_name = breach.get("Name") or breach.get("name") or None
    breach_title = breach.get("Title") or breach.get("title") or None
    breach_date = breach.get("BreachDate") or breach.get("breachDate") or None
    breach_domain = breach.get("Domain") or breach.get("domain") or None

    cur.execute("""
        INSERT INTO email_breaches (target_id, email, breach_name, breach_title, breach_date, breach_domain, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (target_id, email, breach_name, breach_title, breach_date, breach_domain, raw))
    conn.commit()
    conn.close()

def save_source_result(target_id: Optional[int], source: str, type_: str, url: str, score: float, summary: str, raw: dict):
    conn = get_conn()
    cur = conn.cursor()
    raw_text = json.dumps(raw, ensure_ascii=False)
    cur.execute("""
        INSERT INTO source_results (target_id, source, type, url, score, summary, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (target_id, source, type_, url, score, summary, raw_text))
    conn.commit()
    conn.close()


def save_phone_lookup(target_id: Optional[int], numero: str, e164: Optional[str], country: Optional[str], carrier: Optional[str], is_valid: Optional[bool], is_possible: Optional[bool], raw_json: str):
    """
    Sauvegarde un résultat de lookup téléphone.
    raw_json : chaîne JSON (string) contenant le détail / hits web si besoin.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO phone_lookups (target_id, numero, e164, country, carrier, is_valid, is_possible, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (target_id, numero, e164, country, carrier, int(bool(is_valid)) if is_valid is not None else None, int(bool(is_possible)) if is_possible is not None else None, raw_json))
    conn.commit()
    conn.close()
