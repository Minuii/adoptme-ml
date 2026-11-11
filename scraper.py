"""Snapshot Adopt Me data into data/ (plain files, committed to git by the GitHub Action).

    python scraper.py values   # Elvebredd + AMVGG value lists -> data/values/<source>/<time>.json.gz
    python scraper.py trades   # AMVGG completed trades (page only shows the last ~100) -> data/trades/<day>.jsonl
    python scraper.py auto     # trades, plus values if the last value snapshot is older than VALUES_EVERY
"""
import gzip, json, re, sys, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA = Path(__file__).parent / "data"
VALUES_EVERY = timedelta(hours=4, minutes=45)  # ~5 snapshots/day
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"}
PUSH = re.compile(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)')
BADGES = {"N", "M", "F", "R"}


def now():
    return datetime.now(timezone.utc)


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode("utf-8")


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


def auto():
    snapshot_trades()
    last = last_values_time()
    if last is None or now() - last >= VALUES_EVERY:
        snapshot_values()


def load_values(source):
    """All snapshots of one source as a DataFrame: one row per item per snapshot."""
    import pandas as pd
    rows = []
    for f in sorted((DATA / "values" / source).glob("*.json.gz")):
        at = datetime.strptime(f.name[:16], "%Y-%m-%dT%H%MZ").replace(tzinfo=timezone.utc)
        rows += [dict(item, scraped_at=at) for item in json.loads(gzip.decompress(f.read_bytes()))]
    return pd.DataFrame(rows)


def load_trades():
    import pandas as pd
    return pd.DataFrame([json.loads(line) for f in sorted((DATA / "trades").glob("*.jsonl"))
                         for line in f.read_text(encoding="utf-8").splitlines()])


if __name__ == "__main__":
    {"values": snapshot_values, "trades": snapshot_trades, "auto": auto}[sys.argv[1]]()
