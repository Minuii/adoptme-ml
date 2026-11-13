"""Elvebredd's values for the variants its change log doesn't keep, from archived copies of its calculator.

    python scripts/elve_archive.py   # -> data/elve_archive/<capture time>.json.gz (skips captures it already has)

Elvebredd's change log reliably records only three pet variants (normal no potion, neon fly ride, mega fly ride). The
other nine (normal fly ride, the fly-only / ride-only values, neon / mega no potion) have almost no logged history, so
before this site began its own checks (2026-11-11) their charts were empty. web.archive.org saved Elvebredd's calculator
page now and then since mid 2025, and that page carries every item with all twelve pet values. Each saved copy gives
those values on that date (only the date of the copy is known, not when a value changed in between). build_site.py
uses them, with this site's own snapshots after them, for variants whose logged history falls short. Not used by the
model (it reads data/elve_updates only).
"""
import gzip
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # the project folder: scraper.py and friends
from scraper import DATA, UA, find_list

PAGE = "elvebredd.com/adopt-me-calculator"
BEFORE = "20261111103600"  # this site's own snapshots of Elvebredd's list start here
OUT = DATA / "elve_archive"
KEEP = ("id", "name", "type") + tuple(f"{v}value - {p}" for v in "rnm" for p in ("fly&ride", "fly", "ride", "nopotion")) + ("value", "rvalue")


def get(url):
    raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
    return (gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw).decode("utf-8", "replace")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    days = {f.name[:8] for f in OUT.glob("*.json.gz")}
    rows = json.loads(get(f"https://web.archive.org/cdx/search/cdx?url={PAGE}&output=json&fl=timestamp"
                          f"&filter=statuscode:200&to={BEFORE}&collapse=timestamp:8"))[1:]
    for (ts,) in rows:
        if ts[:8] in days or ts >= BEFORE:
            continue
        try:
            items = find_list(get(f"https://web.archive.org/web/{ts}id_/https://{PAGE}"), "initialPets")
        except Exception as e:  # older page layouts have no list; some copies fail to load
            print(ts, "skip:", repr(e)[:80], flush=True)
            time.sleep(3)
            continue
        keep = [{k: i.get(k) for k in KEEP if i.get(k) not in (None, "")} for i in items if i.get("name")]
        if len(keep) < 500:
            print(ts, "skip: only", len(keep), "items", flush=True)
            continue
        (OUT / f"{ts}.json.gz").write_bytes(gzip.compress(json.dumps(keep, separators=(",", ":")).encode(), mtime=0))
        days.add(ts[:8])
        print(ts, len(keep), "items", flush=True)
        time.sleep(3)  # be gentle with archive.org


if __name__ == "__main__":
    main()
