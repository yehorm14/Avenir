"""Generate synthetic TRAINING statements for the matcher with Gemini (free tier).

Usage: python -I m1_gen_statements.py PROCESSED_DIR OUT_JSONL [--per-career 20] [--model gemini-2.5-flash]

For each demo career, asks the model for short first-person "what I enjoy" statements in a
16-18-year-old's voice that would fit someone suited to that career, without naming the job.
Only public ESCO text (career title, description, skills) is sent. The output is training data
only; it never touches the dev or test labels. Reads GEMINI_API_KEY (and GEMINI_API_KEY2 as a
fallback) from the repo's .env. Results are cached per career, so re-runs only fill gaps.
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from ml_common import DEMO  # noqa: E402

BASE = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

PROMPT = """You write realistic, varied first-person statements for a careers quiz dataset.

Career (do NOT name it or any job title in the statements):
Title: {title}
What people in it do: {desc}
Typical skills: {skills}

Write {n} short statements (1 to 3 sentences each) in the voice of different UK 16-18-year-olds
who would be well suited to this career. Vary the voice: chatty, vague, specific, unsure, blunt,
enthusiastic. Mention interests, school subjects, hobbies, things they do at home, what they
dislike, what they want from work. Use everyday words, no jargon, no job titles, no company names.
Return ONLY a JSON array of strings."""


def load_keys(env_path: Path) -> list[str]:
    keys = []
    for line in env_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(GEMINI_API_KEY2?)=(.+)$", line.strip())
        if m:
            keys.append(m.group(2).strip().strip('"'))
    if not keys:
        raise SystemExit("no GEMINI_API_KEY in .env")
    return keys


def ask(key: str, model: str, prompt: str) -> list[str]:
    r = requests.post(BASE, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                      json={"model": model, "temperature": 1.0, "messages": [{"role": "user", "content": prompt}]}, timeout=120)
    if r.status_code == 429:
        raise RuntimeError("rate limited")
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    arr = json.loads(text)
    return [s.strip() for s in arr if isinstance(s, str) and 15 <= len(s.strip()) <= 400]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("processed"); ap.add_argument("out"); ap.add_argument("--per-career", type=int, default=20)
    ap.add_argument("--model", default="gemini-2.5-flash")
    a = ap.parse_args()
    repo = Path(__file__).resolve().parents[3]
    keys = load_keys(repo / ".env")
    texts = json.loads((Path(a.processed) / "career_texts.json").read_text(encoding="utf-8"))
    out = Path(a.out)
    have = {}
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            have.setdefault(rec["soc2020"], []).append(rec)
    ki = 0
    with out.open("a", encoding="utf-8") as fh:
        for soc in DEMO:
            if len(have.get(soc, [])) >= a.per_career:
                continue
            e = texts[soc]
            desc = " ".join(c["text"] for c in e["chunks"][:4])[:1500]
            prompt = PROMPT.format(title=e["title"], desc=desc, skills=", ".join(e["skills"][:10]), n=a.per_career)
            for attempt in range(4):
                try:
                    stmts = ask(keys[ki % len(keys)], a.model, prompt)
                    break
                except Exception as ex:  # noqa: BLE001
                    wait = 20 * (attempt + 1)
                    print(f"{soc}: {ex}; switching key and waiting {wait}s", file=sys.stderr)
                    ki += 1
                    time.sleep(wait)
            else:
                print(f"{soc}: giving up", file=sys.stderr)
                continue
            for s in stmts:
                fh.write(json.dumps({"soc2020": soc, "text": s, "source": a.model, "kind": "synthetic_train"}, ensure_ascii=False) + "\n")
            fh.flush()
            print(f"{soc} {e['short_title']}: {len(stmts)} statements")
            time.sleep(4)  # stay under free-tier requests per minute


if __name__ == "__main__":
    main()
