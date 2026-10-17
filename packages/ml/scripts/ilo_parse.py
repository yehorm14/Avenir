"""Parse the ILO WP140 (2025) GenAI exposure table out of its web page.

Usage: python -I ilo_parse.py PAGE_HTML OUT_CSV

The page lists, per ISCO-08 unit group: exposure gradient, ISCO code, title,
mean exposure score and its standard deviation. Writes one row per ISCO code.
"""
import csv
import html
import re
import sys

ROW = re.compile(r"<tr>(.*?)</tr>", re.S)
CELL = re.compile(r'<p class="table-text">(.*?)</p>', re.S)


def main() -> None:
    page = open(sys.argv[1], encoding="utf-8", errors="replace").read()
    rows = {}
    for tr in ROW.findall(page):
        cells = [html.unescape(re.sub(r"\s+", " ", c)).strip() for c in CELL.findall(tr)]
        if len(cells) != 5 or not re.fullmatch(r"\d{4}", cells[1]):
            continue
        gradient, isco, title, mean, sd = cells
        try:
            rows[isco] = {
                "isco08": isco,
                "title": title,
                "gradient": gradient,
                "exposure_mean": float(mean),
                "exposure_sd": float(sd),
            }
        except ValueError:
            continue
    with open(sys.argv[2], "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["isco08", "title", "gradient", "exposure_mean", "exposure_sd"])
        writer.writeheader()
        for isco in sorted(rows):
            writer.writerow(rows[isco])
    gradients = {}
    for r in rows.values():
        gradients[r["gradient"]] = gradients.get(r["gradient"], 0) + 1
    print(f"{len(rows)} ISCO codes; by gradient: {dict(sorted(gradients.items()))}")


if __name__ == "__main__":
    main()
