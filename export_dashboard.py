"""Summarise data/ into small CSVs for the dashboard artifact -> dashboard_data/*.csv (git-ignored).

    git pull && python export_dashboard.py
"""
import collections, csv, gzip, json
from pathlib import Path

from scraper import DATA, lines

OUT = Path(__file__).parent / "dashboard_data"


def safe_lines(folder):
    try:
        return lines(folder)
    except json.JSONDecodeError:  # a backfill may be mid-write; skip the half line
        rows = []
        for f in sorted((DATA / folder).glob("*.jsonl")):
            for line in f.read_text(encoding="utf-8").splitlines():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return rows


def write(name, rows, cols):
    OUT.mkdir(exist_ok=True)
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerows(rows)
    print(name, len(rows))


def pct(old, new):
    try:
        return round((float(new) - float(old)) / float(old) * 100, 2)
    except (TypeError, ValueError, ZeroDivisionError):
        return ""


elve = [c for c in safe_lines("elve_updates") if "newValue" in c]
gg_raw = safe_lines("amvgg_updates")
gg = [{"when": c["updatedAt"], "item": c["itemName"], "variant": v,
       "old": c.get(f"previous{v}Value"), "new": c[f"new{v}Value"]}
      for c in gg_raw for v in ("Regular", "Neon", "Mega", "Item") if c.get(f"new{v}Value") is not None]
gg_demand = sum(1 for c in gg_raw for v in ("Regular", "Neon", "Mega", "Item") if c.get(f"new{v}Demand") is not None)
trades = safe_lines("trades")
snaps = {s: sorted((DATA / "values" / s).glob("*.json.gz")) for s in ("elve", "amvgg")}
elve_batches = {c["batch"] for c in safe_lines("elve_updates")}

# 1. coverage: one row per kind of data
def span(xs):
    xs = sorted(xs)
    return (xs[0][:10], xs[-1][:10]) if xs else ("", "")

cov = [
    ("elve_changes", "Elvebredd value changes", len(elve), *span(c["effectiveAt"] for c in elve)),
    ("amvgg_changes", "AMVGG value changes", len(gg), *span(c["when"] for c in gg)),
    ("amvgg_demand", "AMVGG demand changes", gg_demand, *span(c["updatedAt"] for c in gg_raw)),
    ("trades", "AMVGG completed trades", len(trades), *span(t["first_seen"] for t in trades)),
    ("elve_snapshots", "Elvebredd value snapshots", len(snaps["elve"]), *span(f.name[:10] for f in snaps["elve"])),
    ("amvgg_snapshots", "AMVGG value snapshots", len(snaps["amvgg"]), *span(f.name[:10] for f in snaps["amvgg"])),
]
write("coverage.csv", [dict(zip(("key", "label", "records", "first", "last"), r)) for r in cov],
      ["key", "label", "records", "first", "last"])

# 2. value changes per month, both sources
monthly = collections.defaultdict(lambda: {"elve": 0, "amvgg": 0, "elve_up": 0, "elve_down": 0, "amvgg_up": 0, "amvgg_down": 0})
for c in elve:
    m = monthly[c["effectiveAt"][:7]]
    m["elve"] += 1
    if c["previousValue"] is not None:
        m["elve_up" if float(c["newValue"]) > float(c["previousValue"]) else "elve_down"] += 1
for c in gg:
    m = monthly[c["when"][:7]]
    m["amvgg"] += 1
    if c["old"] is not None:
        m["amvgg_up" if float(c["new"]) > float(c["old"]) else "amvgg_down"] += 1
write("changes_monthly.csv", [dict(month=k, **v) for k, v in sorted(monthly.items())],
      ["month", "elve", "amvgg", "elve_up", "elve_down", "amvgg_up", "amvgg_down"])

# 3. trades collected per hour
hourly = collections.Counter(t["first_seen"][:13] + ":00Z" for t in trades)
write("trades_hourly.csv", [{"hour": h, "trades": n} for h, n in sorted(hourly.items())], ["hour", "trades"])

# 4. most traded items (count each item once per trade side)
items = collections.Counter(i["name"] for t in trades for s in t["sides"] for i in {i["name"]: i for i in s["items"]}.values())
write("top_traded.csv", [{"item": k, "trades": v} for k, v in items.most_common(25)], ["item", "trades"])

# 5. latest value changes from both lists
recent = [{"when": c["effectiveAt"][:16].replace("T", " "), "source": "Elvebredd", "item": c["name"], "variant": c["label"],
           "old": c["previousValue"] and float(c["previousValue"]), "new": float(c["newValue"]),
           "pct": pct(c["previousValue"], c["newValue"]), "key": f"elve-{c['id']}"} for c in elve]
recent += [{"when": c["when"][:16].replace("T", " "), "source": "AMVGG", "item": c["item"], "variant": c["variant"],
            "old": c["old"] and float(c["old"]), "new": float(c["new"]), "pct": pct(c["old"], c["new"]),
            "key": f"amvgg-{i}"} for i, c in enumerate(gg)]
recent.sort(key=lambda r: r["when"], reverse=True)
write("recent_changes.csv", recent[:60], ["key", "when", "source", "item", "variant", "old", "new", "pct"])

# 6. items whose value changed most often in the last 90 days (both lists)
latest = max([c["effectiveAt"] for c in elve] + [c["when"] for c in gg])[:10]
from datetime import date, timedelta
cut = (date.fromisoformat(latest) - timedelta(days=90)).isoformat()
busy = collections.defaultdict(lambda: {"elve": 0, "amvgg": 0})
for c in elve:
    if c["effectiveAt"][:10] >= cut:
        busy[c["name"]]["elve"] += 1
for c in gg:
    if c["when"][:10] >= cut:
        busy[c["item"]]["amvgg"] += 1
rows = sorted(({"item": k, **v, "total": v["elve"] + v["amvgg"]} for k, v in busy.items()), key=lambda r: -r["total"])
write("most_changed.csv", rows[:20], ["item", "elve", "amvgg", "total"])
print("elve batches stored:", len(elve_batches), "| 90-day window from", cut)
