"""Build the GitHub Pages value list: data/ -> site/data.json (git-ignored; the pages workflow runs this).

    python build_site.py   # then open site/index.html through a local server: python -m http.server -d site
"""
import gzip, json
from pathlib import Path

from scraper import DATA, amvgg_variants, elve_canonical, item_key as key, lines

SITE = Path(__file__).parent / "site"

# Variant code = <r|n|m><potion>, potion: fr fly ride, f fly, r ride, np no potion. Non-pets have one value: "v".
ELVE_SNAP = {f"{v}-{p}": f"{v}value - {k}" for v in "rnm"
             for p, k in (("fr", "fly&ride"), ("f", "fly"), ("r", "ride"), ("np", "nopotion"))}
GG_SNAP = {"r-fr": "regularValue", "n-fr": "neonValue", "m-fr": "megaValue",
           "r-np": "npRegularValue", "n-np": "npNeonValue", "m-np": "npMegaValue",
           "r-r": "rValue", "r-f": "fValue", "n-r": "nrValue", "n-f": "nfValue", "m-r": "mrValue", "m-f": "mfValue"}
ELVE_LABEL = {"default": "r", "neon": "n", "mega": "m", "no potion": "np", "fly ride": "fr"}
GG_KIND = {"petwear": "pet wear", "houses": "other"}  # AMVGG /values/<kind> -> Elvebredd's category names


def num(v):
    try:
        return round(float(v), 4) if v not in (None, "") and float(v) > 0 else None
    except (TypeError, ValueError):
        return None


def latest(source):
    f = sorted((DATA / "values" / source).glob("*.json.gz"))[-1]
    checked = DATA / "values" / "checked.txt"  # lists are read hourly; a file is only written when one changed
    return json.loads(gzip.decompress(f.read_bytes())), max(f.name[:16], checked.read_text(encoding="utf-8").strip() if checked.exists() else "")


elve, elve_at = latest("elve")
gg, gg_at = latest("amvgg")
gg_upd = lines("amvgg_updates")
gg_coef = json.loads((DATA / "amvgg_coefficients.json").read_text(encoding="utf-8")) if (DATA / "amvgg_coefficients.json").exists() else {}
elve_upd = [c for c in lines("elve_updates") if "newValue" in c]
elve_items = elve_canonical(elve, elve_upd)  # one entry per name; Elvebredd lists some items twice
elve_id = {i["id"]: k for k, i in elve_items.items()}
catalog = {key(i["name"]): i for i in json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))} \
    if (DATA / "catalog.json").exists() else {}

items = {}
for k, i in elve_items.items():
    pet = i.get("type") == "pets"
    vals = {v: num(i.get(f)) for v, f in ELVE_SNAP.items()} if pet else {"v": num(i.get("value") or i.get("rvalue"))}
    items[k] = {"name": i["name"], "cat": i.get("type") or "other", "rarity": (i.get("rarity") or "").replace("none", ""),
                             "E": {k: v for k, v in vals.items() if v}, "A": {}, "img": "https://elvebredd.com" + i["image"] if i.get("image") else ""}
for i in gg:
    kind = i.get("kind", "pets")  # snapshots before 2026-11-11 came from the calculator: pets only
    it = items.setdefault(key(i["name"]), {"name": i["name"], "cat": GG_KIND.get(kind, kind), "rarity": "", "E": {}, "A": {}, "img": ""})
    if kind == "pets":
        vals = {v: num(x) for v, x in amvgg_variants(i, gg_coef).items()}  # ride/fly/no potion: derived like amvgg.com does
        dem = {v: i.get(f[:-5] + "Demand") for v, f in GG_SNAP.items()}  # potion demand is only set for a few pets:
        it["demand"] = {v: d or dem[v[0] + "-fr"] for v, d in dem.items() if d or dem[v[0] + "-fr"]}  # else the fly ride one
    else:
        vals = {"v": num(i.get("value"))}
        it["demand"] = {"v": i["demand"]} if i.get("demand") else {}
    it["A"] = {k: v for k, v in vals.items() if v}
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


for c in sorted(elve_upd, key=lambda c: c["effectiveAt"]):
    k = elve_id.get(c.get("petId"))  # by id: the log follows one of an item's duplicate entries
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

elve_ch = elve_upd
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

# ---- Trade ads tab: the newest ads from both sites, items only (owner ids never leave the repo) ----
ADS_KEEP = {"amvgg": 3000, "elve": 1500}  # AMVGG gets ~2,000 ads an hour at peak, Elvebredd ~500


def recent_ads(source):
    files = sorted((DATA / "ads" / source).glob("20*/*.jsonl.gz"))[-60:]
    latest = {}
    for f in files:
        for line in gzip.open(f, "rt", encoding="utf-8"):
            a = json.loads(line)
            if a["id"] not in latest or a["t"] > latest[a["id"]]["t"]:  # Elve listings reappear when renewed
                latest[a["id"]] = a
    return sorted(latest.values(), key=lambda a: a["t"])[-ADS_KEEP[source]:]


tokens, tok_id, ads = [], {}, []
def tok(raw):  # "Name|BADGES" -> index into tokens: [site item name or raw name, badges, on the site?]
    if raw not in tok_id:
        name, _, badge = raw.partition("|")
        it = None if name.startswith("#") else items.get(key(name))
        tok_id[raw] = len(tokens)
        tokens.append([it["name"] if it else name.lstrip("#"), badge, 1 if it else 0])
    return tok_id[raw]


for src, code in (("amvgg", "A"), ("elve", "E")):
    for a in recent_ads(src):
        ads.append([code, a["t"][:16], [tok(x) for x in a["give"]], [tok(x) for x in a["get"]]])
ads.sort(key=lambda a: a[1], reverse=True)
(SITE / "ads.json").write_text(json.dumps({"built": now.isoformat(timespec="minutes"), "tokens": tokens, "ads": ads},
                                          separators=(",", ":")), encoding="utf-8")
print(len(ads), "ads,", len(tokens), "item tokens,", round((SITE / "ads.json").stat().st_size / 1e6, 2), "MB")

if __name__ == "__main__":  # smoke check: a well-known pet joins across both lists with history
    sd = items[key("Shadow Dragon")]
    assert sd["E"].get("m-fr") and sd["A"].get("m-fr") and sd["hist"]["A"].get("m-fr"), sd
