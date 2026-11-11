"""Snapshot Adopt Me data into data/ (plain files, committed to git by the GitHub Action).

    python scraper.py values   # Elvebredd + AMVGG value lists -> data/values/<source>/<time>.json.gz
    python scraper.py trades   # AMVGG completed trades (page only shows the last ~100) -> data/trades/<day>.jsonl
    python scraper.py auto     # trades, plus values + new Elve value updates if the last snapshot is older than VALUES_EVERY
    python scraper.py amvgg-updates # AMVGG's change log (since 2026-06-02) -> data/amvgg_updates/<month>.jsonl
    python scraper.py stats         # rewrite STATS.md
    python scraper.py elve-updates  # Elvebredd's change log (old -> new value per variant, since 2023-09) -> data/elve_updates/<month>.jsonl
"""
import gzip, json, re, sys, time, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA = Path(__file__).parent / "data"
VALUES_EVERY = timedelta(hours=4, minutes=45)  # ~5 snapshots/day
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
            # card = ["$", "div", "<trade id>", {...}]
            if isinstance(n, list) and len(n) == 4 and n[:2] == ["$", "div"] and str(n[2]).isdigit():
                trades[n[2]] = parse_trade(n[3], all_trees)
    return trades


def ts(t):
    return t.strftime("%Y-%m-%dT%H%MZ")  # no colons: valid filename on Windows


def snapshot_values():
    # ponytail: whole list per snapshot (~100KB gz). Diff-only storage if the repo ever gets big.
    for source, url, key in [("elve", "https://elvebredd.com/adopt-me-calculator", "initialPets"),
                             ("amvgg", "https://amvgg.com/calculator", "pets")]:
        items = find_list(fetch(url), key)
        out = DATA / "values" / source / f"{ts(now())}.json.gz"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(gzip.compress(json.dumps(items).encode()))
        print(source, len(items), "items")


def trade_file(day):
    return DATA / "trades" / f"{day:%Y-%m-%d}.jsonl"


def snapshot_trades():
    trades = completed_trades(fetch("https://amvgg.com/trades/completed"))
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
    files = sorted((DATA / "values" / "elve").glob("*.json.gz"))
    if not files:
        return None
    return datetime.strptime(files[-1].name[:16], "%Y-%m-%dT%H%MZ").replace(tzinfo=timezone.utc)


def elve_update_batch(n):
    """Changes in Elvebredd value update #n: dicts with name, label (variant), previousValue, newValue, effectiveAt."""
    trees, seen, best = rsc_trees(fetch(f"https://elvebredd.com/value-updates/{n}")), set(), []
    for t in trees.values():
        for x in walk(t, trees, seen):
            if isinstance(x, list) and x and isinstance(x[0], dict) and "previousValue" in x[0] and len(x) > len(best):
                best = x
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
        rows = elve_update_batch(n)
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


def lines(folder, pattern="*.jsonl"):
    return [json.loads(line) for f in sorted((DATA / folder).glob(pattern))
            for line in f.read_text(encoding="utf-8").splitlines()]


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


def auto():
    snapshot_trades()
    last = last_values_time()
    if last is None or now() - last >= VALUES_EVERY:
        snapshot_values()
        # sync_elve_updates(limit=30)  # re-enable once the local full backfill is pushed (avoids two writers)
        sync_amvgg_updates()
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


def load_trades():
    import pandas as pd
    return pd.DataFrame([json.loads(line) for f in sorted((DATA / "trades").glob("*.jsonl"))
                         for line in f.read_text(encoding="utf-8").splitlines()])


if __name__ == "__main__":
    {"values": snapshot_values, "trades": snapshot_trades, "auto": auto, "elve-updates": sync_elve_updates, "amvgg-updates": sync_amvgg_updates, "stats": write_stats}[sys.argv[1]]()
