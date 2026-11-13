"""Snapshot Adopt Me data into data/ (plain files, committed to git by the GitHub Action).

    python scraper.py values   # Elvebredd + AMVGG value lists -> data/values/<source>/<time>.json.gz
    python scraper.py trades   # AMVGG completed trades (page only shows the last ~100) -> data/trades/<day>.jsonl
    python scraper.py amvgg-ads  # AMVGG trade ads posted since the newest stored one -> data/ads/amvgg/<day>.jsonl
    python scraper.py elve-ads   # sample of Elvebredd's newest trade listings -> data/ads/elve/<day>.jsonl
    python scraper.py auto     # trades + both ad feeds, plus values + new Elve value updates if the last snapshot is older than VALUES_EVERY
    python scraper.py amvgg-updates # AMVGG's change log (since 2026-06-02) -> data/amvgg_updates/<month>.jsonl
    python scraper.py stats         # rewrite STATS.md
    python scraper.py health        # exit 1 if a collector has gone quiet (the bot's last step: a failed run = an email)
    python scraper.py news          # new playadopt.me/news posts (update notes since 2020) -> data/news.jsonl
    python scraper.py elve-updates  # Elvebredd's change log (old -> new value per variant, since 2023-09) -> data/elve_updates/<month>.jsonl
"""
import gzip, json, re, sys, time, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA = Path(__file__).parent / "data"
VALUES_EVERY = timedelta(minutes=55)  # checked hourly (the :00 run); a snapshot file is only written when a list changed
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"}
PUSH = re.compile(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)')
BADGES = {"N", "M", "F", "R"}


def now():
    return datetime.now(timezone.utc)


def fetch(url, tries=5):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code != 429 and e.code < 500 or i == tries - 1:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if i == tries - 1:
                raise
        time.sleep(10 * 2 ** i)  # 10s, 20s, 40s, 80s: rides out rate limits and network blips


def rsc_trees(html):
    """Next.js pages embed their data as 'id:json' lines inside self.__next_f.push calls.
    Returns {line id: parsed json}; lines point at each other with "$L<id>" strings."""
    payload = "".join(json.loads('"' + s + '"') for s in PUSH.findall(html))
    trees = {}
    for line in payload.split("\n"):
        rid, _, body = line.partition(":")
        if body[:1] in "[{":
            try:
                trees[rid] = json.loads(body)
            except json.JSONDecodeError:
                pass  # non-JSON chunk types (text, hints)
    return trees


REF = re.compile(r"\$[L@]?([0-9a-f]+)")


def walk(node, trees, seen=None):
    """Depth-first over a tree, following "$L<id>" references into other lines."""
    seen = set() if seen is None else seen
    if isinstance(node, str):
        m = REF.fullmatch(node)
        if m and m[1] in trees and m[1] not in seen:
            seen.add(m[1])
            yield from walk(trees[m[1]], trees, seen)
        return
    yield node
    children = node.values() if isinstance(node, dict) else node if isinstance(node, list) else ()
    for c in children:
        yield from walk(c, trees, seen)


def find_list(html, key):
    trees, seen = rsc_trees(html), set()
    for tree in trees.values():
        for n in walk(tree, trees, seen):
            if isinstance(n, dict) and isinstance(n.get(key), list) and n[key]:
                return n[key]
    raise RuntimeError(f"no '{key}' list found; page layout changed?")


def parse_trade(node, trees):
    """One completed-trade card -> two sides of {user, user_id, items:[{name, badges}]}."""
    sides = []
    for n in walk(node, trees):
        if not isinstance(n, dict):
            continue
        if "userId" in n and "alt" in n:
            sides.append({"user": n["alt"], "user_id": n["userId"], "items": []})
        elif str(n.get("src", "")).startswith("/items/") and sides:
            sides[-1]["items"].append({"name": n["alt"], "badges": ""})
        elif isinstance(n.get("children"), str) and n["children"] in BADGES and sides and sides[-1]["items"]:
            sides[-1]["items"][-1]["badges"] += n["children"]
    return sides


def completed_trades(html):
    trades, all_trees, seen = {}, rsc_trees(html), set()
    for tree in all_trees.values():
        for n in walk(tree, all_trees, seen):
            # card = ["$", "div", "<trade id>", {...}]; item tiles can also have all-digit keys, but they have no traders
            if isinstance(n, list) and len(n) == 4 and n[:2] == ["$", "div"] and str(n[2]).isdigit():
                sides = parse_trade(n[3], all_trees)
                if sides:
                    trades[n[2]] = sides
    return trades


def ts(t):
    return t.strftime("%Y-%m-%dT%H%MZ")  # no colons: valid filename on Windows


# AMVGG's calculator only has pets (r/n/m fly ride). /values/pets has all 12 pet variants, and every other
# category (eggs, toys, ...) is only on its own /values/<kind> page, under "items" with one value + demand.
AMVGG_KINDS = ["pets", "eggs", "food", "gifts", "houses", "petwear", "stickers", "strollers", "toys", "vehicles"]


def save_amvgg_coefficients(pets_html):
    """AMVGG stores ride / fly / no-potion values for only ~29 pets (category 13). For every other pet its site
    multiplies the fly ride value by a per-category coefficient table that ships inside the pets page's JS chunk.
    Saved to data/amvgg_coefficients.json; amvgg_variants() applies it."""
    chunk = re.search(r'/_next/static/chunks/[^"\ ]*/pets/page-[^"\ ]+\.js', pets_html).group(0)
    table = json.loads(re.search(r"""JSON\.parse\('(\{"0":\{"NP".*?\}\})'\)""", fetch("https://amvgg.com" + chunk)).group(1))
    assert len(table) > 10 and all({"NP", "R", "F", "NNP", "NR", "NF", "MNP", "MR", "MF"} <= set(v) for v in table.values())
    (DATA / "amvgg_coefficients.json").write_text(json.dumps(table, indent=0), encoding="utf-8")


def amvgg_variants(pet, table):
    """A pet's 12 AMVGG values by variant code (r|n|m)-(fr|f|r|np), the way amvgg.com's pets page shows them
    (logic copied from its page chunk, 2026-11-11). Category 13 pets carry explicit values; the rest are derived."""
    from decimal import Decimal, ROUND_HALF_UP
    num = lambda v: float(v) if v not in (None, "") else 0.0
    t, a, r = num(pet.get("regularValue")), num(pet.get("neonValue")), num(pet.get("megaValue"))
    out = {"r-fr": t, "n-fr": a, "m-fr": r}
    cat = pet.get("category")
    if cat == 13 or cat is None:
        out.update({"r-r": num(pet.get("rValue")), "r-f": num(pet.get("fValue")), "r-np": num(pet.get("npRegularValue")),
                    "n-r": num(pet.get("nrValue")), "n-f": num(pet.get("nfValue")), "n-np": num(pet.get("npNeonValue")),
                    "m-r": num(pet.get("mrValue")), "m-f": num(pet.get("mfValue")), "m-np": num(pet.get("npMegaValue"))})
        return out
    c = table.get(str(cat))
    if not c:  # the site shows the fly ride value for every potion in this case
        return {f"{v}-{p}": out[f"{v}-fr"] for v in "rnm" for p in ("fr", "f", "r", "np")}

    def rnd(x, places):  # site: decimal.js round to min(places, 4) decimals (5 when |x| < 0.001)
        places = min(places, 5 if x and abs(x) < .001 else 4)
        return float(Decimal(str(x)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))
    d0 = 3 if t >= .0175 else 5
    if cat == 11 and t > .08:
        out.update({"r-np": rnd(.95 * t, d0), "r-r": rnd(.975 * t, d0), "r-f": rnd(.975 * t, d0),
                    "n-r": a if a > .2 else rnd(a * c["NR"], 5), "n-f": a if a > .2 else rnd(a * c["NF"], 5),
                    "m-r": r if r > .9 else rnd(r * c["MR"], 5), "m-f": r if r > .9 else rnd(r * c["MF"], 5)})
    else:
        out.update({"r-np": rnd(t * c["NP"], d0), "r-r": rnd(t * c["R"], d0), "r-f": rnd(t * c["F"], d0),
                    "n-r": rnd(a * c["NR"], 5), "n-f": rnd(a * c["NF"], 5), "m-r": rnd(r * c["MR"], 5), "m-f": rnd(r * c["MF"], 5)})
    out.update({"n-np": rnd(a * c["NNP"], 5), "m-np": rnd(r * c["MNP"], 5)})
    return out


def snapshot_values():
    # ponytail: whole list per snapshot (~150KB gz). Diff-only storage if the repo ever gets big.
    # a throwaway query string gets a fresh render: on 2026-11-13 amvgg's plain /values/pets URL served a copy ~18 h old
    # (the same Next.js page cache as the trades page), which logged a fake drop and recovery for 46 pets
    bust = f"?t={int(time.time())}"
    lists = {"elve": find_list(fetch("https://elvebredd.com/adopt-me-calculator" + bust), "initialPets"), "amvgg": []}
    for kind in AMVGG_KINDS:
        html = fetch(f"https://amvgg.com/values/{kind}{bust}")
        lists["amvgg"] += [dict(i, kind=kind) for i in find_list(html, "pets" if kind == "pets" else "items")]
        if kind == "pets":
            try:  # a side file: never let it break the snapshot
                save_amvgg_coefficients(html)
            except Exception as e:
                print(f"amvgg coefficients not refreshed: {e!r}")
    stamp = ts(now())
    for source, items in lists.items():
        folder = DATA / "values" / source
        folder.mkdir(parents=True, exist_ok=True)
        old = sorted(folder.glob("*.json.gz"))
        if old and json.loads(gzip.decompress(old[-1].read_bytes())) == items:
            print(source, len(items), "items, unchanged since", old[-1].name[:16])
            continue  # hourly checks mostly find nothing new: a file per change keeps the repo small
        (folder / f"{stamp}.json.gz").write_bytes(gzip.compress(json.dumps(items).encode()))
        print(source, len(items), "items")
    (DATA / "values" / "checked.txt").write_text(stamp, encoding="utf-8")  # when both lists were last read


def trade_file(day):
    return DATA / "trades" / f"{day:%Y-%m-%d}.jsonl"


def snapshot_trades():
    # The plain URL is a Next.js cached page that can be up to 5 min stale (s-maxage=300); a throwaway
    # query string gets a fresh render. At peak (~6 trades/min) the page only spans ~17 min.
    trades = completed_trades(fetch(f"https://amvgg.com/trades/completed?t={int(time.time())}"))
    if not trades:
        raise RuntimeError("no trades parsed; page layout changed?")
    t = now()
    # the page only holds ~1h of trades, so today's + yesterday's files cover every possible duplicate
    seen = {json.loads(line)["trade_id"]
            for f in (trade_file(t), trade_file(t - timedelta(days=1))) if f.exists()
            for line in f.read_text(encoding="utf-8").splitlines()}
    new = [tid for tid in trades if tid not in seen]
    trade_file(t).parent.mkdir(parents=True, exist_ok=True)
    with trade_file(t).open("a", encoding="utf-8") as f:
        for tid in new:
            f.write(json.dumps({"trade_id": tid, "first_seen": t.isoformat(timespec="seconds"),
                                "sides": trades[tid]}) + "\n")
    print(f"{len(trades)} trades on page, {len(new)} new")


def last_values_time():
    checked = DATA / "values" / "checked.txt"
    files = sorted((DATA / "values" / "elve").glob("*.json.gz"))
    stamp = checked.read_text(encoding="utf-8").strip() if checked.exists() else files[-1].name[:16] if files else None
    return datetime.strptime(stamp, "%Y-%m-%dT%H%MZ").replace(tzinfo=timezone.utc) if stamp else None


def elve_update_batch(n):
    """Changes in Elvebredd value update #n: dicts with name, label (variant), previousValue, newValue, effectiveAt."""
    html = fetch(f"https://elvebredd.com/value-updates/{n}")
    trees, seen, best = rsc_trees(html), set(), []
    for t in trees.values():
        for x in walk(t, trees, seen):
            if isinstance(x, list) and x and isinstance(x[0], dict) and "previousValue" in x[0] and len(x) > len(best):
                best = x
    # A batch with no changes is a small page (~120 KB) that never mentions previousValue; a real one is ~2 MB.
    # Finding nothing on a big page means the parser is out of date, not that the batch is empty.
    if not best and ("previousValue" in html or len(html) > 500_000):
        raise RuntimeError(f"value update #{n}: the page has changes but none were parsed; page layout changed?")
    return best


def sync_elve_updates(limit=None):
    """Fetch every update batch not stored yet. Batches with no changes are recorded in empty.jsonl so they aren't refetched."""
    folder = DATA / "elve_updates"
    folder.mkdir(parents=True, exist_ok=True)
    done = {json.loads(line)["batch"] for f in folder.glob("*.jsonl")
            for line in f.read_text(encoding="utf-8").splitlines()}
    latest = max(int(x) for x in re.findall(r"/value-updates/(\d+)", fetch("https://elvebredd.com/")))
    todo = [n for n in range(latest, 0, -1) if n not in done][:limit]  # newest first: recent history matters most
    for i, n in enumerate(todo):
        try:
            rows = elve_update_batch(n)
        except RuntimeError as e:  # not stored, so it is fetched again next run instead of being filed as empty for good
            print(e)
            continue
        out = folder / (rows[0]["effectiveAt"][:7] + ".jsonl" if rows else "empty.jsonl")
        with out.open("a", encoding="utf-8") as f:
            for r in rows or [{}]:
                f.write(json.dumps(dict(r, batch=n)) + "\n")
        if i % 50 == 0:
            print(f"batch {n}: {len(rows)} changes ({i + 1}/{len(todo)})", flush=True)
        time.sleep(1)  # be gentle: each page is ~2MB
    print(f"elve updates synced up to #{latest}, {len(todo)} fetched")


def sync_amvgg_updates():
    """AMVGG value changes (API goes back to 2026-06-02), newest first, until a page is already stored."""
    folder = DATA / "amvgg_updates"
    folder.mkdir(parents=True, exist_ok=True)
    known = {c["id"] for c in lines("amvgg_updates")}
    new, offset = [], 0
    while True:
        page = json.loads(fetch(f"https://amvgg.com/api/value-updates?limit=100&offset={offset}"))["data"]
        fresh = [c for c in page if c["id"] not in known]
        known |= {c["id"] for c in fresh}
        new += fresh
        if not page or not fresh:
            break
        offset += 100
        time.sleep(6)  # the API rate-limits (429) quick bursts
    for c in sorted(new, key=lambda c: c["updatedAt"]):
        with (folder / f"{c['updatedAt'][:7]}.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(c) + "\n")
    print(f"amvgg updates: {len(new)} new")


def health():
    """Exit 1 if a collector has gone quiet. Offer and news failures are only printed (they must not block trades and
    values), and a page-layout change can leave a collector running but finding nothing; this is what notices."""
    def hours(stamp):  # hours since an ISO time, None if there is none
        return None if not stamp else (now() - datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))).total_seconds() / 3600

    def newest(folder, field):  # newest value of a field in a folder's two latest monthly files
        files = sorted(f for f in (DATA / folder).glob("20*.jsonl"))[-2:]
        return max((json.loads(l)[field] for f in files for l in f.read_text(encoding="utf-8").splitlines()), default=None)

    t = now()
    trades = [json.loads(l)["first_seen"] for f in (trade_file(t), trade_file(t - timedelta(days=1))) if f.exists()
              for l in f.read_text(encoding="utf-8").splitlines()]
    last_values = last_values_time()
    news = [json.loads(l).get("published") for l in NEWS.read_text(encoding="utf-8").splitlines()] if NEWS.exists() else []
    checks = [("completed trades", hours(max(trades, default=None)), 3),
              ("AMVGG offers", hours(max((a["t"] for a in recent_ads("amvgg")), default=None)), 6),
              ("Elvebredd offers", hours(max((a["t"] for a in recent_ads("elve")), default=None)), 6),
              ("value lists check", hours(last_values and last_values.isoformat()), 3),
              ("Elvebredd value changes", hours(newest("elve_updates", "effectiveAt")), 5 * 24),
              ("AMVGG value changes", hours(newest("amvgg_updates", "updatedAt")), 7 * 24),
              ("news posts", hours(max((n for n in news if n), default=None)), 21 * 24)]
    late = [(name, age, limit) for name, age, limit in checks if age is None or age > limit]
    for name, age, limit in checks:
        print(f"{'LATE' if (name, age, limit) in late else 'ok  '} {name}: newest is "
              f"{'missing' if age is None else f'{age:.1f} h old'} (limit {limit} h)")
    if late:
        sys.exit(1)


def lines(folder, pattern="*.jsonl"):
    return [json.loads(line) for f in sorted((DATA / folder).glob(pattern))
            for line in f.read_text(encoding="utf-8").splitlines()]


# ---- item names: one join key for Elvebredd, AMVGG, trades, ads and the wiki catalog ----
# Spellings differ only in case, accents, punctuation and a leading "The" ("Mr. Whiskerpips" / "Mr Whiskerpips",
# "Tió" / "Tio", "The Black Dog" / "Black Dog"), plus a few typos, mapped here to Elvebredd's spelling. Checked by hand
# 2026-11-11; unsure pairs (Copter Hat/Cap, Fly-A-Pet Potion/... Forever) are left unmatched.
NAME_ALIASES = {"magpie wings": "mapgie wings", "eco brown earth wizard hat": "eco brown eath wizard hat",
                "velvet fuchsia mega neon paint": "velvet fuschia mega neon paint", "ruddy duck waddler": "ruddy ducky waddler",
                "chihuaha": "chihuahua",
                # Elvebredd's names for AMVGG's "Fly-A-Pet Potion" / "Ride-A-Pet Potion" (same item: the two lists'
                # values differ by the ~170x scale gap every other potion shows)
                "fly a pet potion forever": "fly a pet potion", "ride a pet potion forever": "ride a pet potion"}


def item_key(name):
    import unicodedata
    s = unicodedata.normalize("NFKD", str(name).lower().replace("’", "'"))
    s = re.sub(r"[^a-z0-9 ]+", " ", "".join(c for c in s if not unicodedata.combining(c)).replace("'", ""))
    s = re.sub(r"^the ", "", " ".join(s.split()))
    return NAME_ALIASES.get(s, s)


def elve_canonical(items, updates):
    """Elvebredd lists some items twice (case variants, old copies), sometimes with different values. Keep, per
    item_key, the id its change log actually follows (most logged changes), then the higher `score`."""
    logged = {}
    for c in updates:
        logged[c.get("petId")] = logged.get(c.get("petId"), 0) + 1
    best = {}
    for i in items:
        if not i.get("name") or str(i["name"]).lower() == "nan":
            continue
        k, rank = item_key(i["name"]), (logged.get(i.get("id"), 0), i.get("score") or 0)
        if k not in best or rank > best[k][0]:
            best[k] = (rank, i)
    return {k: i for k, (_, i) in best.items()}


def num(v):
    return "-" if v is None else f"{float(v):g}"  # None = item had no value before (newly added)


def write_stats():
    """STATS.md at the repo root: a human-readable view of what has been collected so far."""
    def side(s):
        names = [i["name"] + (f" ({i['badges']})" if i["badges"] else "") for i in s["items"]]
        items = ", ".join(n + (f" ×{names.count(n)}" if names.count(n) > 1 else "") for n in dict.fromkeys(names))
        return f"**{s['user']}**: {items}".replace("|", "/")

    trades = lines("trades")
    per_day = {}
    for t in trades:
        per_day[t["first_seen"][:10]] = per_day.get(t["first_seen"][:10], 0) + 1
    snaps = {s: sorted((DATA / "values" / s).glob("*.json.gz")) for s in ("elve", "amvgg")}
    changes = [c for c in lines("elve_updates") if "newValue" in c]
    changes.sort(key=lambda c: c["effectiveAt"])

    out = [f"# Collected data\n\n_Updated {now():%Y-%m-%d %H:%M} UTC by the scrape workflow._\n",
           "## Value snapshots\n", "| Source | Snapshots | First | Latest |", "|---|---|---|---|"]
    out += [f"| {s} | {len(f)} | {f[0].name[:16] if f else '-'} | {f[-1].name[:16] if f else '-'} |" for s, f in snaps.items()]
    out += ["\n## Offers (trade listings) collected by the bot\n", "| Source | Days | Offers today + yesterday | Newest offer |", "|---|---|---|---|"]
    for src in ("amvgg", "elve"):
        days = [d for d in (DATA / "ads" / src).glob("20*") if d.is_dir()]
        recent = recent_ads(src)
        out.append(f"| {src} | {len(days)} | {len(recent):,} | {max((a['t'][:16] for a in recent), default='-')} |")
    out += [f"\n## AMVGG completed trades: {len(trades):,} total\n", "| Day (UTC) | Trades |", "|---|---|"]
    out += [f"| {d} | {n:,} |" for d, n in sorted(per_day.items(), reverse=True)[:14]]
    out += ["\n### Latest 15\n", "| Seen (UTC) | Side A | Side B |", "|---|---|---|"]
    out += [f"| {t['first_seen'][11:16]} | {side(t['sides'][0])} | {side(t['sides'][1]) if len(t['sides']) > 1 else ''} |"
            for t in trades[-15:][::-1]]
    if changes:
        out += [f"\n## Elvebredd value changes: {len(changes):,} since {changes[0]['effectiveAt'][:10]}\n",
                "| When (UTC) | Item | Variant | Old | New |", "|---|---|---|---|---|"]
        out += [f"| {c['effectiveAt'][:16].replace('T', ' ')} | {c['name']} | {c['label']} | "
                f"{num(c['previousValue'])} | {num(c['newValue'])} |" for c in changes[-15:][::-1]]
    gg = sorted(lines("amvgg_updates"), key=lambda c: c["updatedAt"])
    if gg:
        def moves(c):
            vals = [f"{v} {num(c.get('previous' + v + 'Value'))} → {num(c['new' + v + 'Value'])}"
                    for v in ("Regular", "Neon", "Mega", "Item") if c.get("new" + v + "Value") is not None]
            dem = [f"{v} demand {c.get('previous' + v + 'Demand')} → {c['new' + v + 'Demand']}"
                   for v in ("Regular", "Neon", "Mega", "Item") if c.get("new" + v + "Demand") is not None]
            return ", ".join(vals + dem)
        out += [f"\n## AMVGG value changes: {len(gg):,} since {gg[0]['updatedAt'][:10]}\n",
                "| When (UTC) | Item | Changes |", "|---|---|---|"]
        out += [f"| {c['updatedAt'][:16].replace('T', ' ')} | {c['itemName']} | {moves(c)} |" for c in gg[-15:][::-1]]
    (DATA.parent / "STATS.md").write_text("\n".join(out) + "\n", encoding="utf-8")


# ---- trade ads ("I give X, I want Y" listings) ----
# AMVGG: /api/trades pages backwards in time with a cursor, so every ad can be collected (owner approved).
# Elvebredd: /api/recent-listings. Page 0 = the 50 most recently posted or auto-renewed listings (~5 per second),
#   deeper offsets = archive sorted by last update, oldest first. Only sampling is feasible. robots.txt disallows /api;
#   use approved by David (head value manager) on 2026-11-11.
AMVGG_ADS = "https://amvgg.com/api/trades?limit=100"
ELVE_ADS = "https://elvebredd.com/api/recent-listings?limit=50&offset={}&game=Adopt+Me"


def amvgg_ad(a):
    def item(i):  # signs ("Add", "Upgrade", ...) have no name, only an image path
        name = i.get("name") or "#" + (i.get("sign") or "?").rsplit("/", 1)[-1].split(".")[0]
        return f"{name}|{(i.get('type') or '').upper()}"
    return {"id": a["id"], "t": a["publishedAt"], "owner": a.get("authorRobloxId"),
            "give": [item(i) for i in a.get("offering") or []], "get": [item(i) for i in a.get("lookingFor") or []]}


def elve_ad(x):
    def item(i):
        a = i.get("attributes") or {}
        code = ("M" if a.get("mega") else "N" if a.get("neon") else "") + ("F" if a.get("fly") else "") + ("R" if a.get("ride") else "")
        return f"{i['name']}|{code}" + (f"|{i['mutation']}" if i.get("mutation") else "")
    return {"id": x["id"], "created": x["timeCreated"], "t": x["timeUpdated"], "owner": x.get("ownerRobloxID"),
            "diff": x.get("difference"), "give": [item(i) for i in x.get("ownerGive") or []],
            "get": [item(i) for i in x.get("ownerGet") or []]}


def save_ads(source, ads, key):
    """New ads -> data/ads/<source>/<day of t>/<run time>.jsonl.gz. One small gzip per run: git stores each ad once,
    compressed, instead of a growing text file per commit. Skips keys already stored today or yesterday."""
    folder = DATA / "ads" / source
    seen = {key(a) for a in recent_ads(source)}
    new = list({key(a): a for a in ads if key(a) not in seen}.values())
    by_day = {}
    for a in sorted(new, key=lambda a: a["t"]):
        by_day.setdefault(a["t"][:10], []).append(a)
    for day, rows in by_day.items():
        (folder / day).mkdir(parents=True, exist_ok=True)
        out = folder / day / f"{ts(now())}.jsonl.gz"
        old = gzip.decompress(out.read_bytes()).decode() if out.exists() else ""
        out.write_bytes(gzip.compress((old + "".join(json.dumps(a) + "\n" for a in rows)).encode()))
    return len(new)


def recent_ads(source):
    """Ads the bot stored today and yesterday."""
    t = now()
    return [json.loads(l) for d in (t - timedelta(days=1), t)
            for f in sorted((DATA / "ads" / source / f"{d:%Y-%m-%d}").glob("*.jsonl.gz"))
            for l in gzip.decompress(f.read_bytes()).decode().splitlines()]


def sync_amvgg_ads(max_pages=4):
    """AMVGG ads posted since the newest one stored, at most max_pages x 100. At peak ~100 ads/min are posted,
    so daytime runs keep a sample (the newest ~400 per 15 min) and quiet hours are complete."""
    last = max((a["t"] for a in recent_ads("amvgg")), default=None)
    ads, cursor = [], None
    for p in range(max_pages):
        d = json.loads(fetch(AMVGG_ADS + (f"&cursor={cursor}" if cursor else "")))
        ads += [amvgg_ad(a) for a in d["trades"]]
        cursor = d["pagination"].get("nextCursor")
        if last is None or not d["trades"] or d["trades"][-1]["publishedAt"] <= last or not cursor:
            break
        time.sleep(6)
    n = save_ads("amvgg", [a for a in ads if last is None or a["t"] > last], key=lambda a: a["id"])
    print(f"amvgg ads: {n} new")


def sync_elve_ads(samples=3, gap=10):
    """Sample Elve's newest 50 listings a few times; a listing counts again when it is renewed (new t)."""
    ads = []
    for i in range(samples):
        if i:
            time.sleep(gap)
        ads += [elve_ad(x) for x in json.loads(fetch(ELVE_ADS.format(0)))["listings"] if x.get("game") == "Adopt Me"]
    n = save_ads("elve", ads, key=lambda a: (a["id"], a["t"]))
    print(f"elve ads: {n} new")


# ---- playadopt.me/news: one post per game update (weekly, usually Friday 15:00-16:00 UTC), back to 2020 ----
NEWS = DATA / "news.jsonl"


def parse_news(html, slug):
    """Title, exact publish time (the <time dateTime>; the sitemap's lastmod is a bulk-import date for older posts)
    and the post's visible text, including image alt texts, which name the new pets."""
    trees, parts, published = rsc_trees(html), [], None
    for tree in trees.values():
        for n in walk(tree, trees, set()):
            if not isinstance(n, dict):
                continue
            if published is None and isinstance(n.get("dateTime"), str):
                published = n["dateTime"]
            kids = n.get("children")
            kids = [kids] if isinstance(kids, str) else kids if isinstance(kids, list) else []
            parts += [k.strip() for k in kids if isinstance(k, str) and k.strip() and not k.startswith("$")]
            if isinstance(n.get("alt"), str):
                parts.append(n["alt"].strip())
    text = "\n".join(parts)
    title = re.search(r"<title>([^<]*)", html)
    title = title[1].replace(" - Adopt Me!", "").replace("&#x27;", "'").replace("&amp;", "&") if title else slug
    start = text.find(title)
    end = text.find("Play Adopt Me Now!", start)
    return {"slug": slug, "title": title, "published": published,
            "text": text[start if start >= 0 else 0:end if end > 0 else None]}


def sync_news():
    seen = {json.loads(l)["slug"] for l in NEWS.read_text(encoding="utf-8").splitlines()} if NEWS.exists() else set()
    slugs = re.findall(r"/news/([^<\s]+)</loc>", fetch("https://www.playadopt.me/sitemap.xml"))
    new = [s for s in dict.fromkeys(slugs) if s not in seen]
    n = 0
    with NEWS.open("a", encoding="utf-8") as f:
        for slug in new:  # each post is written as soon as it's read, so an interrupted run resumes where it stopped
            try:
                post = parse_news(fetch(f"https://www.playadopt.me/news/{slug}"), slug)
            except urllib.error.HTTPError as e:  # the sitemap lists at least one dead post (404); try again next run
                print(f"news: {slug} -> HTTP {e.code}")
                continue
            f.write(json.dumps(post, ensure_ascii=False) + "\n")
            f.flush()
            n += 1
            time.sleep(1)
    print(f"news: {n} new posts")


def load_news():
    import pandas as pd
    df = pd.DataFrame(lines("", "news.jsonl")).drop_duplicates("slug")
    df["published"] = pd.to_datetime(df["published"], utc=True, format="ISO8601")
    return df.dropna(subset=["published"]).sort_values("published").reset_index(drop=True)


def auto():
    snapshot_trades()
    last = last_values_time()
    due = last is None or now() - last >= VALUES_EVERY
    # on the hourly values run, take one Elve ad sample instead of three (saves 20 s of waiting, keeps the run short)
    for job in (sync_amvgg_ads, (lambda: sync_elve_ads(samples=1)) if due else sync_elve_ads):
        try:  # ads are a side signal: never let them break trade/value collection
            job()
        except Exception as e:
            print(f"ads job failed: {e!r}")
    if due:
        snapshot_values()
        sync_elve_updates(limit=30)
        sync_amvgg_updates()
        try:  # update notes are a side signal too
            sync_news()
        except Exception as e:
            print(f"news job failed: {e!r}")
    write_stats()


def load_values(source):
    """All snapshots of one source as a DataFrame: one row per item per snapshot."""
    import pandas as pd
    rows = []
    for f in sorted((DATA / "values" / source).glob("*.json.gz")):
        at = datetime.strptime(f.name[:16], "%Y-%m-%dT%H%MZ").replace(tzinfo=timezone.utc)
        rows += [dict(item, scraped_at=at) for item in json.loads(gzip.decompress(f.read_bytes()))]
    return pd.DataFrame(rows)


def load_elve_updates():
    """Every Elvebredd value change: one row per item variant per update, oldest first."""
    import pandas as pd
    df = pd.DataFrame([json.loads(line) for f in sorted((DATA / "elve_updates").glob("*.jsonl"))
                       for line in f.read_text(encoding="utf-8").splitlines()])
    df = df.dropna(subset=["newValue"])
    df["effectiveAt"] = pd.to_datetime(df["effectiveAt"], utc=True, format="ISO8601")
    for c in ("previousValue", "newValue", "change"):
        df[c] = df[c].astype(float)
    return df.sort_values(["effectiveAt", "batch"]).reset_index(drop=True)


def load_amvgg_updates():
    """Every AMVGG change, long format: one row per item per variant per update.
    variant = Regular/Neon/Mega for pets, Item for everything else. A row can be a value change, a demand change, or both."""
    import pandas as pd
    rows = [{"id": c["id"], "name": c["itemName"], "category": c.get("itemCategory"), "variant": v,
             "previousValue": c.get(f"previous{v}Value"), "newValue": c.get(f"new{v}Value"),
             "previousDemand": c.get(f"previous{v}Demand"), "newDemand": c.get(f"new{v}Demand"), "updatedAt": c["updatedAt"]}
            for c in lines("amvgg_updates") for v in ("Regular", "Neon", "Mega", "Item")
            if c.get(f"new{v}Value") is not None or c.get(f"new{v}Demand") is not None]
    df = pd.DataFrame(rows)
    df["updatedAt"] = pd.to_datetime(df["updatedAt"], utc=True, format="ISO8601")
    for c in ("previousValue", "newValue"):
        df[c] = pd.to_numeric(df[c])
    return df.sort_values("updatedAt").reset_index(drop=True)


def load_ads(source):
    """Trade ads from the bot (data/ads/<source>/<day>/*.jsonl.gz) and the sampled backfill (backfill/*.jsonl.gz), one row
    per ad sighting. Elve listings repeat when renewed: dedupe on (id, t) here, or on id for unique listings."""
    import pandas as pd
    folder = DATA / "ads" / source
    rows = [json.loads(l) for f in sorted(folder.glob("*/*.jsonl.gz")) for l in gzip.open(f, "rt", encoding="utf-8")]
    df = pd.DataFrame(rows).drop_duplicates(subset=["id", "t"])
    df["t"] = pd.to_datetime(df["t"], utc=True, format="ISO8601")
    return df.sort_values("t").reset_index(drop=True)


def load_trades():
    import pandas as pd
    return pd.DataFrame([json.loads(line) for f in sorted((DATA / "trades").glob("*.jsonl"))
                         for line in f.read_text(encoding="utf-8").splitlines()])


if __name__ == "__main__":
    {"values": snapshot_values, "trades": snapshot_trades, "auto": auto,
     "amvgg-ads": sync_amvgg_ads, "elve-ads": sync_elve_ads, "elve-updates": sync_elve_updates, "amvgg-updates": sync_amvgg_updates, "news": sync_news, "stats": write_stats, "health": health}[sys.argv[1]]()
