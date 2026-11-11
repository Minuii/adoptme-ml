"""Build the GitHub Pages value list: data/ -> site/data.json (git-ignored; the pages workflow runs this).

    python build_site.py   # then open site/index.html through a local server: python -m http.server -d site
"""
import gzip, json
from pathlib import Path

from scraper import DATA, lines

SITE = Path(__file__).parent / "site"

# Variant code = <r|n|m><potion>, potion: fr fly ride, f fly, r ride, np no potion. Non-pets have one value: "v".
ELVE_SNAP = {f"{v}-{p}": f"{v}value - {k}" for v in "rnm"
             for p, k in (("fr", "fly&ride"), ("f", "fly"), ("r", "ride"), ("np", "nopotion"))}
GG_SNAP = {"r-fr": "regularValue", "n-fr": "neonValue", "m-fr": "megaValue",
           "r-np": "npRegularValue", "n-np": "npNeonValue", "m-np": "npMegaValue",
           "r-r": "rValue", "r-f": "fValue", "n-r": "nrValue", "n-f": "nfValue", "m-r": "mrValue", "m-f": "mfValue"}
ELVE_LABEL = {"default": "r", "neon": "n", "mega": "m", "no potion": "np", "fly ride": "fr"}
GG_CAT = {"PetWear": "pet wear", "Vehicles": "vehicles", "Houses": "other"}


def key(name):
    return " ".join(str(name).lower().replace("’", "'").split())


def num(v):
    try:
        return round(float(v), 4) if v not in (None, "") and float(v) > 0 else None
    except (TypeError, ValueError):
        return None


def latest(source):
    f = sorted((DATA / "values" / source).glob("*.json.gz"))[-1]
    return json.loads(gzip.decompress(f.read_bytes())), f.name[:16]


elve, elve_at = latest("elve")
gg, gg_at = latest("amvgg")
gg_upd = lines("amvgg_updates")
gg_cat = {key(c["itemName"]): c.get("itemCategory") for c in gg_upd}
catalog = {key(i["name"]): i for i in json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))} \
    if (DATA / "catalog.json").exists() else {}

items = {}
for i in elve:
    if not i.get("name"):
        continue
    pet = i.get("type") == "pets"
    vals = {v: num(i.get(f)) for v, f in ELVE_SNAP.items()} if pet else {"v": num(i.get("value") or i.get("rvalue"))}
    items[key(i["name"])] = {"name": i["name"], "cat": i.get("type") or "other", "rarity": (i.get("rarity") or "").replace("none", ""),
                             "E": {k: v for k, v in vals.items() if v}, "A": {}, "img": "https://elvebredd.com" + i["image"] if i.get("image") else ""}
for i in gg:
    it = items.setdefault(key(i["name"]), {"name": i["name"], "cat": GG_CAT.get(gg_cat.get(key(i["name"])), str(gg_cat.get(key(i["name"])) or "other").lower()),
                                           "rarity": "", "E": {}, "A": {}, "img": ""})
    pet = it["cat"] == "pets"
    vals = {v: num(i.get(f)) for v, f in GG_SNAP.items()} if pet else {"v": num(i.get("regularValue"))}
    it["A"] = {k: v for k, v in vals.items() if v}
    it["demand"] = {v: i.get(f"{n}Demand") for v, n in (("r", "regular"), ("n", "neon"), ("m", "mega")) if i.get(f"{n}Demand")}
for k, it in items.items():
    c = catalog.get(k)
    if c:
        it["img"] = c.get("thumbnail") or it["img"]
        it["rarity"] = it["rarity"] or c.get("rarity", "").replace("_", " ").replace("-", " ")
        it["origin"] = c.get("origin", "")
    it["hist"] = {"E": {}, "A": {}}


def add(k, src, v, t, old, new):
    it = items.get(k)
    if not it or new is None:
        return
    h = it["hist"][src].setdefault(v, [])
    if not h and old is not None:  # value before the first recorded change
        h.append([t, old])
    h.append([t, new])


for c in sorted((c for c in lines("elve_updates") if "newValue" in c), key=lambda c: c["effectiveAt"]):
    k = key(c["name"])
    if k not in items:
        continue
    v = "-".join(ELVE_LABEL.get(p, p) for p in c["label"].split(" ", 1)) if items[k]["cat"] == "pets" else "v"
    add(k, "E", v, c["effectiveAt"][:16], num(c["previousValue"]), num(c["newValue"]))
for c in sorted(gg_upd, key=lambda c: c["updatedAt"]):
    k = key(c["itemName"])
    for col, v in (("Regular", "r-fr"), ("Neon", "n-fr"), ("Mega", "m-fr"), ("Item", "v")):
        if k in items and items[k]["cat"] != "pets" and col != "Item":
            v = "v" if col == "Regular" else None  # non-pets: AMVGG keeps the value in Regular or Item
        if v and c.get(f"new{col}Value") is not None:
            add(k, "A", v, c["updatedAt"][:16], num(c.get(f"previous{col}Value")), num(c[f"new{col}Value"]))

out = [it for it in items.values() if it["E"] or it["A"]]
SITE.mkdir(exist_ok=True)
(SITE / "data.json").write_text(json.dumps({"elve_at": elve_at, "amvgg_at": gg_at, "items": out},
                                           separators=(",", ":")), encoding="utf-8")
print(len(out), "items,", sum(bool(i["A"]) for i in out), "on AMVGG,", sum(bool(i["E"]) for i in out), "on Elvebredd,",
      round((SITE / "data.json").stat().st_size / 1e6, 2), "MB")

# ---- Stats tab: what has been collected so far (aggregates only; no trader names leave the repo) ----
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

elve_ch = [c for c in lines("elve_updates") if "newValue" in c]
gg_ch = [(c["updatedAt"], c["itemName"], v) for c in gg_upd for v in ("Regular", "Neon", "Mega", "Item") if c.get(f"new{v}Value") is not None]
gg_dem = sum(1 for c in gg_upd for v in ("Regular", "Neon", "Mega", "Item") if c.get(f"new{v}Demand") is not None)
trades = lines("trades")
now = datetime.now(timezone.utc)
ago = lambda days: (now - timedelta(days=days)).isoformat()[:16]

monthly = defaultdict(lambda: [0, 0])
for c in elve_ch:
    monthly[c["effectiveAt"][:7]][0] += 1
for t, _, _ in gg_ch:
    monthly[t[:7]][1] += 1
busy = defaultdict(lambda: [0, 0])
for c in elve_ch:
    if c["effectiveAt"][:16] >= ago(90):
        busy[c["name"]][0] += 1
for t, name, _ in gg_ch:
    if t[:16] >= ago(90):
        busy[name][1] += 1
week = [t for t in trades if t["first_seen"][:16] >= ago(7)]
traded = Counter(n for t in week for s in t["sides"] for n in {i["name"] for i in s["items"]})
hourly = Counter(t["first_seen"][:13] for t in trades if t["first_seen"][:16] >= ago(3))
snaps = {s: sorted((DATA / "values" / s).glob("*.json.gz")) for s in ("elve", "amvgg")}

stats = {
    "built": now.isoformat(timespec="minutes"),
    "totals": {"elve_changes": len(elve_ch), "elve_first": min(c["effectiveAt"] for c in elve_ch)[:10],
               "amvgg_changes": len(gg_ch), "amvgg_first": min(t for t, _, _ in gg_ch)[:10], "amvgg_demand": gg_dem,
               "trades": len(trades), "trades_first": min((t["first_seen"] for t in trades), default="")[:10],
               "trades_24h": sum(t["first_seen"][:16] >= ago(1) for t in trades),
               "snapshots": len(snaps["elve"]) + len(snaps["amvgg"])},
    "monthly": [[m, e, a] for m, (e, a) in sorted(monthly.items())],
    "hourly": sorted(hourly.items()),
    "traded_7d": traded.most_common(20),
    "busy_90d": sorted(([n, e, a] for n, (e, a) in busy.items()), key=lambda r: -(r[1] + r[2]))[:20],
}
(SITE / "stats.json").write_text(json.dumps(stats, separators=(",", ":")), encoding="utf-8")
print("stats:", stats["totals"])

if __name__ == "__main__":  # smoke check: a well-known pet joins across both lists with history
    sd = items[key("Shadow Dragon")]
    assert sd["E"].get("m-fr") and sd["A"].get("m-fr") and sd["hist"]["A"].get("m-fr"), sd
