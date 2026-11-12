"""Checks for the fragile parts of scraper.py: name matching and the Next.js page parser. No network.

    python test_scraper.py      # or: pytest test_scraper.py
"""
import json

import scraper


def page(*lines):
    """A fake Next.js page: each line 'id:json' goes out in its own self.__next_f.push call, as the real sites do."""
    return "".join(f"<script>self.__next_f.push([1,{json.dumps(l + chr(10))}])</script>" for l in lines)


def test_item_key():
    k = scraper.item_key
    assert k("The Black Dog") == k("black dog") == "black dog"
    assert k("Tió De Nadal") == k("Tio de Nadal")
    assert k("Mr. Whiskerpips") == k("Mr Whiskerpips")
    assert k("Skele-Rex") == k("Skele-rex")
    assert k("Chihuaha") == "chihuahua"                       # typo alias
    assert k("Cat") != k("Cat Dragon")
    assert k("St. Bernard’s") == k("St Bernard's")            # curly and straight apostrophes


def test_elve_canonical_keeps_the_logged_copy():
    items = [{"id": 1, "name": "Skele-Rex", "score": 9}, {"id": 2, "name": "Skele-rex", "score": 1}, {"id": 3, "name": "nan"}]
    log = [{"petId": 2}, {"petId": 2}, {"petId": 1}]
    out = scraper.elve_canonical(items, log)
    assert list(out) == ["skele rex"] and out["skele rex"]["id"] == 2
    assert scraper.elve_canonical(items, [])["skele rex"]["id"] == 1  # no log: the higher score wins


def test_find_list_follows_references():
    html = page('0:{"props":{"data":"$L1"}}', '1:{"initialPets":[{"name":"Cat"},{"name":"Dog"}]}')
    assert [p["name"] for p in scraper.find_list(html, "initialPets")] == ["Cat", "Dog"]
    try:
        scraper.find_list(html, "missing")
    except RuntimeError:
        pass
    else:
        raise AssertionError("a missing list must raise, not return nothing")


def test_completed_trades():
    side = lambda user, uid, item, badge: [{"userId": uid, "alt": user}, {"src": f"/items/{item}.png", "alt": item}, {"children": badge}]
    card = ["$", "div", "12345", {"children": side("ann", 1, "Bat Dragon", "F") + side("bob", 2, "Owl", "N")}]
    tile = ["$", "div", "777", {"children": [{"src": "/items/Cat.png", "alt": "Cat"}]}]  # item tile: digits, no traders
    trades = scraper.completed_trades(page("0:" + json.dumps([card, tile])))
    assert list(trades) == ["12345"]
    a, b = trades["12345"]
    assert (a["user"], a["items"]) == ("ann", [{"name": "Bat Dragon", "badges": "F"}])
    assert (b["user_id"], b["items"][0]["badges"]) == (2, "N")


def test_amvgg_variants():
    v = scraper.amvgg_variants({"regularValue": "1", "neonValue": "4", "megaValue": "16", "category": 0},
                               {"0": {"NP": .08, "R": .5, "F": .6, "NNP": .1, "NR": .5, "NF": .6, "MNP": .1, "MR": .5, "MF": .6}})
    assert (v["r-fr"], v["r-np"], v["r-r"], v["r-f"]) == (1.0, 0.08, 0.5, 0.6)
    assert (v["n-np"], v["m-f"]) == (0.4, 9.6)
    no_table = scraper.amvgg_variants({"regularValue": "1", "neonValue": "4", "megaValue": "16", "category": 99}, {})
    assert no_table["r-np"] == 1.0 and no_table["m-r"] == 16.0  # unknown category: the fly ride value everywhere
    explicit = scraper.amvgg_variants({"regularValue": "2", "category": 13, "rValue": "1.5", "npRegularValue": ""}, {})
    assert explicit["r-r"] == 1.5 and explicit["r-np"] == 0.0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
