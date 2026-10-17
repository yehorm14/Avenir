import json
import sqlite3
from pathlib import Path

DEFAULT_DATABASE = Path(__file__).resolve().parents[1] / "data" / "aventir.sqlite3"


def connect(path=DEFAULT_DATABASE):
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def initialise(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS careers (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, search_text TEXT NOT NULL,
          group_name TEXT NOT NULL, featured INTEGER NOT NULL DEFAULT 0, payload TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS careers_title ON careers(title COLLATE NOCASE);
        CREATE TABLE IF NOT EXISTS series (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS metadata (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
    """)


def save_career(conn, career):
    search_text = " ".join([career["title"]] + career.get("aliases", [])).lower()
    conn.execute(
        "INSERT OR REPLACE INTO careers VALUES (?,?,?,?,?,?)",
        (
            career["id"],
            career["title"],
            search_text,
            career["group"],
            int(career.get("featured", False)),
            json.dumps(career, ensure_ascii=False),
        ),
    )


def get_career(conn, career_id):
    row = conn.execute("SELECT payload FROM careers WHERE id=?", (career_id,)).fetchone()
    return json.loads(row[0]) if row else None


def catalogue(conn, query="", group="", offset=0, limit=30):
    where, args = [], []
    if query:
        # Escape LIKE metacharacters so user searches are literal.
        literal = query.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        where.append("search_text LIKE ? ESCAPE '\\'")
        args.append("%" + literal + "%")
    if group:
        where.append("group_name=?")
        args.append(group)
    clause = " WHERE " + " AND ".join(where) if where else ""
    total = conn.execute("SELECT COUNT(*) FROM careers" + clause, args).fetchone()[0]
    rows = conn.execute(
        "SELECT payload FROM careers"
        + clause
        + " ORDER BY featured DESC, title COLLATE NOCASE LIMIT ? OFFSET ?",
        args + [limit, offset],
    )
    return {"total": total, "offset": offset, "limit": limit, "items": [json.loads(r[0]) for r in rows]}


def get_json(conn, table, key):
    if table not in ("series", "metadata"):
        raise ValueError("Invalid table")
    row = conn.execute("SELECT payload FROM " + table + " WHERE id=?", (key,)).fetchone()
    return json.loads(row[0]) if row else None
