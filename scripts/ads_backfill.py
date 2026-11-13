"""One-off, resumable, sampled backfill of trade-ad history. Run locally (slow); the bot only collects new ads.

    python scripts/ads_backfill.py amvgg   # 1 page (100 ads, ~10 min) per hour of history since late Aug 2026, ~6 s per request
    python scripts/ads_backfill.py elve    # 1 page (50 listings) every STEP offsets of Elve's archive (Feb 2025 ->), ~1.5 s per request

Writes data/ads/<source>/backfill/<month>.jsonl.gz (gzip members appended in chunks) and a progress file of finished
sample points, so it can be stopped and restarted. Kept apart from the bot's data/ads/<source>/<day>.jsonl files.
"""
import gzip, json, sys, time
from datetime import datetime, timedelta, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # the project folder: scraper.py and friends
import scraper

AMVGG_FROM = datetime(2026, 8, 20, tzinfo=timezone.utc)  # earliest ads found are ~Aug 25; empty pages before are cheap
ELVE_PAGES = 10_000  # sample points across the whole archive (~500k listings)


def out_dir(source):
    d = scraper.DATA / "ads" / source / "backfill"
    d.mkdir(parents=True, exist_ok=True)
    return d


def flush(source, ads):
    by_month = {}
    for a in ads:
        by_month.setdefault(a["t"][:7], []).append(a)
    for m, rows in by_month.items():
        with gzip.open(out_dir(source) / f"{m}.jsonl.gz", "at", encoding="utf-8") as f:
            f.writelines(json.dumps(a) + "\n" for a in rows)


def patient(fn, *args):
    """Retry through network drops (PC sleep, Wi-Fi blips): wait up to ~2 h before giving up."""
    for wait in [30] * 10 + [300] * 24:
        try:
            return fn(*args)
        except OSError as e:  # URLError, timeouts, connection resets
            print(f"network error ({e}); retrying in {wait}s", flush=True)
            time.sleep(wait)
    return fn(*args)


def run(source, points, fetch_point, delay):
    progress = out_dir(source) / "progress.txt"
    done = set(progress.read_text().split()) if progress.exists() else set()
    todo = [p for p in points if str(p) not in done]
    print(f"{source}: {len(todo)} of {len(points)} sample points left", flush=True)
    buf, finished = [], []
    for i, p in enumerate(todo):
        buf += patient(fetch_point, p)
        finished.append(str(p))
        if len(finished) >= 20 or i == len(todo) - 1:  # write data first, then mark points done
            flush(source, buf)
            with progress.open("a") as f:
                f.write("\n".join(finished) + "\n")
            print(f"{source}: {i + 1}/{len(todo)} points, last {p}, {len(buf)} ads in chunk", flush=True)
            buf, finished = [], []
        time.sleep(delay)


def amvgg():
    start = AMVGG_FROM
    end = scraper.now().replace(minute=0, second=0, microsecond=0)
    hours = [(start + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%S.000Z") for h in range(int((end - start).total_seconds() // 3600))]

    def page(cursor):  # the 100 ads published just before `cursor`
        return [scraper.amvgg_ad(a) for a in json.loads(scraper.fetch(scraper.AMVGG_ADS + f"&cursor={cursor}"))["trades"]]
    run("amvgg", hours, page, delay=6)


def elve():
    def get(off):
        return [x for x in json.loads(scraper.fetch(scraper.ELVE_ADS.format(off)))["listings"] if x.get("game") == "Adopt Me"]
    # archive end: past it the API falls back to the newest listings instead of an empty page, so "past the end" =
    # page updated within the last hour. Pages near offset 0-1000 are odd, so search from 1M upward.
    cutoff = (scraper.now() - timedelta(hours=1)).isoformat()[:19]
    real = lambda off: any(x["timeUpdated"][:19] < cutoff for x in patient(get, off))
    lo, hi = 1_000_000, 2_000_000
    while real(hi):
        lo, hi = hi, hi * 2
        time.sleep(1)
    while hi - lo > 10_000:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if real(mid) else (lo, mid)
        time.sleep(1)
    step = lo // ELVE_PAGES
    print(f"elve archive ends near offset {lo:,}; sampling every {step:,}", flush=True)
    # sample points are stored as offset fractions so a restart (archive grown) keeps its progress
    points = [f"{k}/{ELVE_PAGES}" for k in range(ELVE_PAGES)]
    run("elve", points, lambda p: [scraper.elve_ad(x) for x in get(int(p.split("/")[0]) * step)], delay=1.5)


if __name__ == "__main__":
    {"amvgg": amvgg, "elve": elve}[sys.argv[1]]()
