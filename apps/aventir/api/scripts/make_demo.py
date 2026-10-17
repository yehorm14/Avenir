"""Export a frozen demo subset from an existing import; no network requests."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aventir.database import DEFAULT_DATABASE, connect, get_json

TITLES = [
    "software developer",
    "data analyst",
    "electrical engineer",
    "civil engineer",
    "land surveyor",
    "mechanical engineer",
    "graphic designer",
    "architect",
    "accountant",
    "secondary school teacher",
    "electrician",
    "industrial designer",
    "web developer",
    "physiotherapist",
    "psychologist",
    "dental practitioner",
    "3d animator",
    "chemical engineer",
    "aerospace engineer",
    "wind turbine technician",
]


def main():
    if not DEFAULT_DATABASE.exists():
        raise SystemExit("Import the live database before regenerating demo fixtures.")
    conn = connect()
    careers = []
    for title in TITLES:
        row = conn.execute("SELECT payload FROM careers WHERE lower(title)=?", (title,)).fetchone()
        if not row:
            raise ValueError("Occupation missing from import: " + title)
        career = json.loads(row[0])
        career["data_status"] = "sample"
        careers.append(career)
    meta = get_json(conn, "metadata", "catalogue")
    meta.update(
        {
            "occupation_count": len(careers),
            "catalogue": "Frozen demo subset of the ESCO API catalogue",
            "enriched_profiles": sum(bool(c["salary"]) for c in careers),
            "matched_titles": [c["title"] for c in careers if c["salary"]],
            "unavailable_skill_profiles": sum(c.get("skills_available") is False for c in careers),
            "mode": "mock",
            "data_status": "sample",
        }
    )
    series = [json.loads(r[0]) for r in conn.execute("SELECT payload FROM series ORDER BY id")]
    conn.close()
    target = Path(__file__).resolve().parents[1] / "fixtures" / "demo.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {"schema_version": "1.0", "metadata": meta, "careers": careers, "industries": series},
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(f"Exported {len(careers)} sample careers and {len(series)} frozen industry series to {target}")


if __name__ == "__main__":
    main()
