"""Live track record of the daily forecasts (7, 30 and 90 days): score each day's calls once their days are over.

    from track_record import record
    R = record(log_folder, snapshots, checked_at)   # build_site.py puts R into site/forecast.json (Stats tab)

Each day `elve_model.py forecast` saves its calls to results/forecast_log/30d/<as-of day>.csv.gz. A day is scored when
the bot has checked Elvebredd's list after the end of (as-of day + 30). Both values come from the site's own snapshots of
Elvebredd's list (written whenever the list changes, so complete since 2026-11-11): the value at the end of the as-of
day, and at the end of the day 30 days later. The scores match the walk-forward backtest (elve_model.py both mode,
"gradient boosting + offers + events"), so the two can be compared:
  - "likely up" calls that rose 2 / 5 / 10%+ (7 / 30 / 90 days), "likely down" calls that dropped as much (the model's classes)
  - the top 20 by P(up) - P(down) (only above 0), their mean change; and the mean change of every pet variant
Standard library only: build_site.py runs on GitHub Pages without pandas.
"""
import csv
import gzip
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HORIZON = 30
# a move under this is "no clear move", as in the model (elve_model.FLAT): 2% at 7 days, 5% at 30, 10% at 90
FLAT_PCT = {7: 0.02, 30: 0.05, 90: 0.10}
TOP_K = 20
KEYS = {"default no potion": "r-np", "neon fly ride": "n-fr", "mega fly ride": "m-fr"}


def load_log(folder):
    """{as-of day: [rows]} from <folder>/<YYYY-MM-DD>.csv.gz."""
    out = {}
    for f in sorted(Path(folder).glob("*.csv.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            out[date.fromisoformat(f.name[:10])] = list(csv.DictReader(fh))
    return out


def value_at(snapshots, t):
    """Values {item key: {variant: value}} of the newest snapshot taken up to time t, or None if there is none.
    snapshots: [(datetime UTC, values)], oldest first."""
    best = None
    for st, vals in snapshots:
        if st > t:
            break
        best = vals
    return best


def score_day(rows, base, after, key, flat=0.05):
    """Scores for one day's calls. base / after: snapshot values at the end of the as-of day / H days later.
    flat: the move (as a fraction) a call must reach to count as right."""
    FLAT = math.log1p(flat)
    moves = []  # (row, log change)
    for r in rows:
        k, v = key(r["name"]), KEYS.get(r["label"])
        b, a = (base.get(k) or {}).get(v), (after.get(k) or {}).get(v)
        if v and b and a:
            moves.append((r, math.log(a / b)))
    up = [m for r, m in moves if r["call"] == "up"]
    dn = [m for r, m in moves if r["call"] == "down"]
    ranked = sorted(((float(r["p_up"]) - float(r["p_down"]), m) for r, m in moves), key=lambda x: -x[0])
    top = [m for s, m in ranked if s > 0][:TOP_K]
    mean = lambda xs: sum(math.expm1(x) for x in xs) / len(xs) if xs else None
    return {"n": len(moves), "up_calls": len(up), "up_hits": sum(m > FLAT for m in up),
            "down_calls": len(dn), "down_hits": sum(m < -FLAT for m in dn),
            "top20": mean(top), "all": mean([m for _, m in moves])}


def record(log_folder, snapshots, checked_at, key, horizon=HORIZON, only_days=None):
    """Scored days, days still waiting, and pooled totals. checked_at: when the bot last read the lists (datetime UTC).
    only_days: score just these as-of days (to compare two models on the same days)."""
    flat = FLAT_PCT.get(horizon, 0.05)
    log = load_log(log_folder)
    if only_days is not None:
        log = {d: rows for d, rows in log.items() if d in only_days}
    scored, waiting = [], []
    for d, rows in sorted(log.items()):
        start = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) + timedelta(days=1)  # end of the as-of day
        end = start + timedelta(days=horizon)
        base, after = value_at(snapshots, start), value_at(snapshots, end)
        if end > checked_at or base is None or after is None:
            waiting.append(d)
            continue
        scored.append({"asof": d.isoformat(), "scored_on": (end.date() - timedelta(days=1)).isoformat(),
                       **score_day(rows, base, after, key, flat)})
    tot = lambda f: sum(s[f] for s in scored)
    avg = lambda f: (lambda xs: sum(xs) / len(xs) if xs else None)([s[f] for s in scored if s[f] is not None])
    return {
        "horizon": horizon, "flat": flat, "first": min(log).isoformat() if log else None,
        "days_logged": len(log), "days_scored": len(scored), "days_waiting": len(waiting),
        "next_result": (min(waiting) + timedelta(days=horizon + 1)).isoformat() if waiting else None,
        "up_calls": tot("up_calls"), "up_hits": tot("up_hits"), "down_calls": tot("down_calls"), "down_hits": tot("down_hits"),
        "up_rate": tot("up_hits") / tot("up_calls") if scored and tot("up_calls") else None,
        "down_rate": tot("down_hits") / tot("down_calls") if scored and tot("down_calls") else None,
        "top20": avg("top20"), "all": avg("all"),
        "days": scored[-60:],
    }
