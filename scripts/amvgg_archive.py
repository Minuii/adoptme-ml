"""amvgg's pet values before its own change log starts (2026-06-02), from archived copies on web.archive.org.

    python scripts/amvgg_archive.py   # -> data/amvgg_archive/<capture time>.json.gz (skips captures it already has)

amvgg keeps no history older than its change log (its /value-updates feed and API end at 2026-06-02, and its pet pages
show only today's value). But the Wayback Machine saved its calculator, home and value-list pages now and then, and
those pages carry the full pet list. Each saved copy gives every pet's normal / neon / mega fly ride value on that date.
Only the dates of the copies are known, not when a value changed between two of them. build_site.py adds these as
earlier points to amvgg's value history. The model doesn't use them (it uses data/amvgg_updates only).
"""
import gzip
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # the project folder: scraper.py and friends
from scraper import DATA, UA, find_list

PAGES = ["amvgg.com/calculator", "amvgg.com/", "amvgg.com/values", "amvgg.com/values/pets"]
BEFORE = "20260602"  # amvgg's own change log covers everything from here on
OUT = DATA / "amvgg_archive"
KEEP = ("name", "regularValue", "neonValue", "megaValue")


def get(url):
    raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
    return (gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw).decode("utf-8", "replace")


def captures():
    """(timestamp, page) of every saved copy before BEFORE, at most one per page per day."""
    out = set()
    for page in PAGES:
        rows = json.loads(get(f"https://web.archive.org/cdx/search/cdx?url={page}&output=json&fl=timestamp"
                              f"&filter=statuscode:200&to={BEFORE}&collapse=timestamp:8"))[1:]
        out |= {(r[0], page) for r in rows}
        time.sleep(2)
    return sorted(out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    have = {f.name[:14] for f in OUT.glob("*.json.gz")}
    done_days = {f.name[:8] for f in OUT.glob("*.json.gz")}
    for ts, page in captures():
        if ts in have or ts[:8] in done_days:
            continue
        try:
            html = get(f"https://web.archive.org/web/{ts}id_/https://{page}")
            pets = find_list(html, "pets")
        except Exception as e:  # older page layouts have no pet list; some copies fail to load
            print(ts, page, "skip:", repr(e)[:80], flush=True)
            time.sleep(3)
            continue
        rows = [{k: p.get(k) for k in KEEP} for p in pets if p.get("name")]
        if len(rows) < 100:
            print(ts, page, "skip: only", len(rows), "pets", flush=True)
            continue
        (OUT / f"{ts}.json.gz").write_bytes(gzip.compress(json.dumps(rows, separators=(",", ":")).encode(), mtime=0))
        done_days.add(ts[:8])
        print(ts, page, len(rows), "pets", flush=True)
        time.sleep(3)  # be gentle with archive.org


if __name__ == "__main__":
    main()
