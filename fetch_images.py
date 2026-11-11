"""Official item catalog + thumbnails from the Adopt Me wiki (playadopt.me/discover).

    python fetch_images.py   # -> data/catalog.json, data/images/<category>/<kind>.png (skips files it already has)
"""
import json, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

from scraper import DATA, UA, fetch, find_list

CATEGORIES = ["pets", "accessories", "transport", "strollers", "food", "toys", "gifts"]

catalog = []
for cat in CATEGORIES:
    items = find_list(fetch(f"https://www.playadopt.me/discover/{cat}"), "items")
    catalog += [dict(i, category=cat) for i in items]
    print(cat, len(items), flush=True)
    time.sleep(1)
(DATA / "catalog.json").write_text(json.dumps(catalog, indent=0), encoding="utf-8")

def image_path(i):
    return DATA / "images" / i["category"] / f"{i.get('kind') or i['id']}.png"  # 4 food items have no kind


def download(i):
    out = image_path(i)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        out.write_bytes(urllib.request.urlopen(urllib.request.Request(i["thumbnail"], headers=UA), timeout=30).read())
    except Exception as e:  # a missing thumbnail shouldn't stop the rest
        print("skip", out.name, e, flush=True)


todo = [i for i in catalog if i.get("thumbnail") and not image_path(i).exists()]
with ThreadPoolExecutor(8) as pool:  # small static files on an image CDN
    for n, _ in enumerate(pool.map(download, todo), 1):
        if n % 250 == 0:
            print(n, "/", len(todo), "images", flush=True)
print("catalog", len(catalog), "items; downloaded", len(todo))
