"""Checks for track_record.py with made-up forecasts and snapshots. No network.

    python tests/test_track_record.py      # or: pytest tests
"""
import csv
import gzip
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # the project folder: scraper.py and friends
from track_record import record, score_day, value_at

UTC = timezone.utc
key = str.lower


def rows(*rs):
    return [dict(zip(("name", "label", "p_up", "p_down", "call"), r)) for r in rs]


def test_value_at_takes_newest_snapshot_up_to_t():
    snaps = [(datetime(2026, 1, 1, 10, tzinfo=UTC), {"a": 1}), (datetime(2026, 1, 2, 10, tzinfo=UTC), {"a": 2})]
    assert value_at(snaps, datetime(2026, 1, 1, 9, tzinfo=UTC)) is None
    assert value_at(snaps, datetime(2026, 1, 2, 0, tzinfo=UTC)) == {"a": 1}
    assert value_at(snaps, datetime(2026, 1, 9, tzinfo=UTC)) == {"a": 2}


def test_score_day():
    base = {"cat": {"r-np": 10, "n-fr": 10}, "dog": {"m-fr": 100}, "owl": {"r-np": 4}}
    after = {"cat": {"r-np": 10.6, "n-fr": 10.4}, "dog": {"m-fr": 90}, "owl": {"r-np": 4}}
    r = score_day(rows(("Cat", "default no potion", .7, .1, "up"),   # +6%: an up hit
                       ("Cat", "neon fly ride", .6, .1, "up"),       # +4%: under 5%, a miss
                       ("Dog", "mega fly ride", .1, .6, "down"),     # -10%: a down hit
                       ("Owl", "default no potion", .2, .3, "flat"),  # score below 0: not a top-20 pick
                       ("Bat", "mega fly ride", .9, 0, "up")), base, after, key)  # not in the snapshots: skipped
    assert (r["n"], r["up_calls"], r["up_hits"], r["down_calls"], r["down_hits"]) == (4, 2, 1, 1, 1)
    assert abs(r["top20"] - (0.06 + 0.04) / 2) < 1e-9          # Cat x2 only (Dog and Owl score below 0)
    assert abs(r["all"] - (0.06 + 0.04 - 0.10 + 0) / 4) < 1e-9


def test_threshold_follows_the_horizon():
    base, after = {"cat": {"r-np": 10}}, {"cat": {"r-np": 10.3}}  # +3%: a hit at 7 days (2%), a miss at 30 days (5%)
    r = rows(("Cat", "default no potion", .7, .1, "up"))
    assert score_day(r, base, after, key, flat=0.02)["up_hits"] == 1
    assert score_day(r, base, after, key, flat=0.05)["up_hits"] == 0


def test_record_waits_for_the_outcome():
    with tempfile.TemporaryDirectory() as d:
        with gzip.open(Path(d) / "2026-01-01.csv.gz", "wt", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, ["name", "label", "p_up", "p_down", "call"])
            w.writeheader()
            w.writerows(rows(("Cat", "default no potion", .7, .1, "up")))
        snaps = [(datetime(2026, 1, 1, 12, tzinfo=UTC), {"cat": {"r-np": 10}}),
                 (datetime(2026, 1, 20, tzinfo=UTC), {"cat": {"r-np": 11}}),
                 (datetime(2026, 2, 1, 1, tzinfo=UTC), {"cat": {"r-np": 50}})]  # after the 30 days: must not count
        early = record(d, snaps, datetime(2026, 1, 31, 23, tzinfo=UTC), key)
        assert (early["days_scored"], early["days_waiting"], early["next_result"]) == (0, 1, "2026-02-01")
        done = record(d, snaps, datetime(2026, 2, 1, 2, tzinfo=UTC), key)
        assert (done["days_scored"], done["up_hits"], done["up_rate"]) == (1, 1, 1.0)
        assert abs(done["top20"] - 0.1) < 1e-9 and done["days"][0]["scored_on"] == "2026-01-31"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
