import sqlite3
import json
import os

DB_PATH = os.getenv("DB_PATH", "investa.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS known_properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                street TEXT NOT NULL,
                city TEXT NOT NULL,
                source TEXT DEFAULT 'manual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                subject TEXT,
                extracted_data TEXT,  -- JSON
                enrichment_data TEXT, -- JSON
                score REAL,
                score_breakdown TEXT, -- JSON
                score_reasoning TEXT,
                is_duplicate INTEGER DEFAULT 0,
                rejection_email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Seed known properties
        existing = conn.execute("SELECT COUNT(*) FROM known_properties").fetchone()[0]
        if existing == 0:
            seeds = [
                ("Bürgerstraße 44", "Berlin"),
                ("Friedrichstraße 100", "Berlin"),
                ("Mönckebergstraße 5", "Hamburg"),
                ("Schwanebecker Chaussee", "Bernau bei Berlin"),
            ]
            conn.executemany("INSERT INTO known_properties (street, city) VALUES (?,?)", seeds)
        conn.commit()

def get_known_properties():
    with get_conn() as conn:
        rows = conn.execute("SELECT street, city FROM known_properties").fetchall()
        return [{"street": r["street"], "city": r["city"]} for r in rows]

def save_known_property(street: str, city: str):
    with get_conn() as conn:
        conn.execute("INSERT INTO known_properties (street, city, source) VALUES (?,?,'auto')", (street, city))
        conn.commit()

def save_offer(filename, subject, extracted_data, enrichment_data, score, score_breakdown, score_reasoning, is_duplicate, rejection_email=None):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO offers (filename, subject, extracted_data, enrichment_data, score, score_breakdown, score_reasoning, is_duplicate, rejection_email)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            filename, subject,
            json.dumps(extracted_data, ensure_ascii=False),
            json.dumps(enrichment_data, ensure_ascii=False),
            score,
            json.dumps(score_breakdown, ensure_ascii=False),
            score_reasoning,
            1 if is_duplicate else 0,
            rejection_email
        ))
        conn.commit()

def get_all_offers():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM offers ORDER BY created_at DESC").fetchall()
        result = []
        for r in rows:
            d = dict(r)
            for f in ["extracted_data", "enrichment_data", "score_breakdown"]:
                if d.get(f):
                    d[f] = json.loads(d[f])
            result.append(d)
        return result