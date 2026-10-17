"""List and download ONS ASHE Table 14 editions (earnings by 4-digit SOC).

All editions sit on one ONS dataset page. The script reads the page, finds the .zip
links, keeps one edition per year (revised if published, otherwise provisional), and
unzips each into data/raw/ashe/<edition>/.

    python scripts/fetch/ons_ashe.py --list
    python scripts/fetch/ons_ashe.py --years 2011-2025
    python scripts/fetch/ons_ashe.py --years 2025 --dry-run

Classification: 2011 revised to 2020 use SOC 2010; 2021 onwards use SOC 2020 (verify in the
files' notes). Never mix codes without the relationship tables in data/raw/crosswalks/.
"""
from __future__ import annotations

import argparse
import re
import zipfile
from html import unescape

from _common import RAW, die, download, session

PAGE = ("https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/"
        "datasets/occupation4digitsoc2010ashetable14")
ZIP_RE = re.compile(r'href="(/file\?uri=[^"]+?\.zip)"', re.I)


def editions(html: str) -> dict[str, str]:
    """Map edition folder (e.g. '2024revised') to absolute download URL."""
    out: dict[str, str] = {}
    for href in ZIP_RE.findall(html):
        href = unescape(href)
        parts = href.split("/")
        edition = parts[-2] if len(parts) >= 2 else href
        out.setdefault(edition, "https://www.ons.gov.uk" + href)
    return out


def pick_per_year(eds: dict[str, str], years: set[int]) -> dict[str, str]:
    """One edition per year: prefer SOC 2010 based (matters for 2011), then revised."""
    best: dict[int, str] = {}
    rank = lambda ed: ("soc2010" in ed, "revised" in ed)  # noqa: E731
    for ed in eds:
        m = re.match(r"(\d{4})", ed)
        if m and int(m.group(1)) in years:
            y = int(m.group(1))
            if y not in best or rank(ed) > rank(best[y]):
                best[y] = ed
    return {best[y]: eds[best[y]] for y in sorted(best)}


def parse_years(spec: str) -> set[int]:
    if "-" in spec:
        a, b = spec.split("-")
        return set(range(int(a), int(b) + 1))
    return {int(y) for y in spec.split(",")}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="list editions found on the page")
    ap.add_argument("--years", default="2011-2025")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    s = session()
    r = s.get(PAGE, timeout=30)
    r.raise_for_status()
    eds = editions(r.text)
    if not eds:
        die("no .zip links found; the ONS page layout may have changed, download by hand")
    if args.list:
        for ed, url in sorted(eds.items()):
            print(f"{ed:40s} {url}")
        return

    for ed, url in pick_per_year(eds, parse_years(args.years)).items():
        dest = RAW / "ashe" / f"{ed}.zip"
        if args.dry_run:
            print(f"would fetch {ed}: {url}")
            continue
        download(s, url, dest)
        target = RAW / "ashe" / ed
        if not target.exists():
            with zipfile.ZipFile(dest) as z:
                z.extractall(target)
            print(f"  unzipped to data/raw/ashe/{ed}/")


if __name__ == "__main__":
    main()
