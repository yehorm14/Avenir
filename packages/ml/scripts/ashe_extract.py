"""Extract ASHE Table 14 annual-pay workbooks from the ONS zip downloads.

Usage: python -I ashe_extract.py OUT_DIR ZIP [ZIP ...]

Each zip goes into its own folder OUT_DIR/<year>_<edition>/, and only the
annual gross pay table (14.7a) and its coefficient-of-variation table (14.7b)
are written. Member names are reduced to their base name, so a zip cannot
write outside its folder.
"""
import re
import sys
import zipfile
from pathlib import Path

WANTED = re.compile(r"Table 14\.7[ab]\s", re.IGNORECASE)


def edition_of(member_names: list[str]) -> tuple[str, str]:
    """Return (year, edition) from the member file names."""
    for name in member_names:
        m = re.search(r"Table 14\.7a.*?(\d{4})\.xlsx?$", name)
        if m:
            year = m.group(1)
            base = Path(name).name
            if base.upper().startswith("PROV"):
                return year, "provisional"
            if base.upper().startswith("REVISED"):
                return year, "revised"
            return year, "revised_or_final"
    raise ValueError("no Table 14.7a in archive")


def extract(zip_path: Path, out_dir: Path) -> Path:
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        year, edition = edition_of(names)
        dest = out_dir / f"{year}_{edition}"
        dest.mkdir(parents=True, exist_ok=True)
        for name in names:
            base = Path(name).name
            if not base or not WANTED.search(base):
                continue
            target = dest / base
            target.write_bytes(zf.read(name))
        (dest / "SOURCE.md").write_text(
            f"Extracted from {zip_path.name}\n"
            "Source: ONS, Earnings and hours worked, occupation by four-digit SOC: ASHE Table 14\n"
            "Licence: Open Government Licence v3.0\n",
            encoding="utf-8",
        )
    return dest


def main() -> None:
    out_dir = Path(sys.argv[1])
    for arg in sys.argv[2:]:
        dest = extract(Path(arg), out_dir)
        files = sorted(p.name for p in dest.iterdir())
        print(f"{Path(arg).name} -> {dest.name}: {len(files) - 1} tables")


if __name__ == "__main__":
    main()
