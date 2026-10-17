"""Reproducible official ESCO + ONS import. Run from apps/aventir/api."""

import concurrent.futures
import json
import math
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aventir.database import DEFAULT_DATABASE, connect, initialise, save_career
from aventir.ingest import normalise_occupation, normalise_series

ESCO = "https://ec.europa.eu/esco/api/search"
CACHE = Path(__file__).resolve().parents[1] / "data" / "raw"
SECTORS = {
    "technology": ("JP9P", "Information & communication"),
    "manufacturing": ("JP9I", "Manufacturing"),
    "construction": ("JP9L", "Construction"),
    "health": ("JP9W", "Human health & social work"),
}


def fetch(url, params=None):
    for attempt in range(4):
        try:
            response = httpx.get(
                url,
                params=params,
                timeout=100,
                follow_redirects=True,
                headers={"User-Agent": "Aventir-Hackathon/0.1 (public research data)"},
            )
            if response.status_code == 500 and "More than one value found" in response.text:
                # Source data error: retrying the identical request cannot repair it.
                response.raise_for_status()
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            if isinstance(exc, httpx.HTTPStatusError) and "More than one value found" in exc.response.text:
                raise
            if attempt == 3:
                raise
            time.sleep(1 + attempt * 2)


def block(start, size=100):
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / (f"occupations-{start}-{size}.json")
    if cached.exists():
        result = json.loads(cached.read_text())
        return result["items"], result["total"]
    try:
        data = fetch(
            ESCO,
            {"type": "occupation", "language": "en", "limit": size, "offset": start // size, "full": "true"},
        )
        result = {
            "items": [normalise_occupation(c) for c in data["_embedded"]["results"]],
            "total": data["total"],
        }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 500:
            raise
        if size > 1:
            smaller = {100: 20, 20: 5, 5: 1}[size]
            batches = [block(s, smaller) for s in range(start, start + size, smaller)]
            result = {"items": [c for batch, _ in batches for c in batch], "total": batches[0][1]}
        else:
            data = fetch(
                ESCO, {"type": "occupation", "language": "en", "limit": 1, "offset": start, "full": "false"}
            )
            result = {
                "items": [normalise_occupation(c) for c in data["_embedded"]["results"]],
                "total": data["total"],
            }
            print(
                "Upstream skill error: retained occupation identity, "
                f"marked skills unavailable at record {start}",
                flush=True,
            )
    cached.write_text(json.dumps(result, ensure_ascii=False))
    return result["items"], result["total"]


def main():
    DEFAULT_DATABASE.parent.mkdir(parents=True, exist_ok=True)
    temporary = DEFAULT_DATABASE.with_suffix(".import.sqlite3")
    if temporary.exists():
        temporary.unlink()
    conn = connect(temporary)
    initialise(conn)
    first, total = block(0)
    occupations = list(first)
    print(f"ESCO: {total} official profiles; importing {math.ceil(total / 100)} pages", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(block, start) for start in range(100, total, 100)]
        for future in concurrent.futures.as_completed(futures):
            batch, batch_total = future.result()
            if batch_total != total:
                raise RuntimeError("ESCO catalogue changed during import; retry")
            occupations.extend(batch)
            print(f"Imported {len(occupations)} / {total}", flush=True)
    # Individually reviewed equivalents only. No salary/sector inference for the wider catalogue.
    enrichment = json.loads((Path(__file__).parent / "enrichment.json").read_text())
    matches = []
    for career in occupations:
        extra = enrichment.get(career["title"].lower())
        if extra:
            career.update(extra)
            matches.append(career["title"])
        save_career(conn, career)
    actual = conn.execute("SELECT count(*) FROM careers").fetchone()[0]
    if actual != total:
        raise RuntimeError(f"Incomplete catalogue: {actual} / {total}")
    now = datetime.now(UTC).isoformat()
    for sector, (code, label) in SECTORS.items():
        url = f"https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/timeseries/{code.lower()}/unem/data"
        raw = fetch(url)
        payload = {
            "id": sector,
            "code": code,
            "name": label,
            "title": raw["description"]["title"],
            "source_url": url.removesuffix("/data"),
            "retrieved_at": now,
            "release_date": raw["description"].get("releaseDate"),
            "unit": "vacancies",
            "geography": "United Kingdom",
            "granularity": "industry",
            "frequency": "Monthly observations of three-month averages",
            "period_labels": {
                datetime.strptime(p["date"].title(), "%Y %b").strftime("%Y-%m-01"): p.get("label", p["date"])
                for p in raw["months"]
            },
            "points": normalise_series(raw),
        }
        conn.execute("INSERT OR REPLACE INTO series VALUES (?,?)", (sector, json.dumps(payload)))
        print("ONS {}: {} real observations".format(code, len(payload["points"])), flush=True)
    meta = {
        "retrieved_at": now,
        "occupation_count": actual,
        "source_reported_total": total,
        "catalogue": "Complete occupation catalogue returned by the ESCO API",
        "esco_source": "https://esco.ec.europa.eu/en/classification/occupation_main",
        "esco_api": ESCO,
        "esco_version": "API default; version not declared by response",
        "enriched_profiles": len(matches),
        "matched_titles": matches,
        "unavailable_skill_profiles": sum(not c["skills_available"] for c in occupations),
        "limitations": (
            "ESCO is a European occupational taxonomy. UK salary references and industry vacancy series "
            "cover reviewed matches only. Industry vacancies are not occupation-level demand or forecasts."
        ),
    }
    conn.execute("INSERT OR REPLACE INTO metadata VALUES (?,?)", ("catalogue", json.dumps(meta)))
    conn.commit()
    conn.close()
    temporary.replace(DEFAULT_DATABASE)
    print(
        f"Verified complete: {actual} careers, {len(matches)} reviewed enrichments. Saved {DEFAULT_DATABASE}",
        flush=True,
    )


if __name__ == "__main__":
    main()
