"""Trade-ad demand features: how much a pet is wanted vs offered in AMVGG and Elvebredd trade ads.

    from ad_features import ad_features
    A = ad_features(days, names)   # long table: day, name, kind + feature columns, to merge into the model panel

The two sites were sampled at very different rates (bot: every ad it sees; backfills: 1 page per hour on AMVGG,
10,000 pages spread over Elvebredd's archive), so everything is a share of that source's ads in a window, never a count.
A feature for day t only uses ads posted up to the end of day t (UTC).
"""
import gzip
import json
from collections import Counter

import numpy as np
import pandas as pd

import scraper

SOURCES = ("elve", "amvgg")  # Elvebredd ads go back to 2025-02, AMVGG's to 2026-08-20
MIN_MENTIONS = 300           # pet mentions needed in a window before its shares mean anything
SMOOTH = 0.5                 # added to every count, so a pet with no ads gets a small share instead of log(0)


def kind_of(badges):
    return "mega" if "M" in badges else "neon" if "N" in badges else "default"


def mentions(names):
    """Ad counts per (source, day, side, pet name, kind). `names` maps item_key -> the model's pet name; anything else
    (toys, potions, "Add" requests, pets outside the model) is ignored. A pet counts once per ad side."""
    counts = Counter()
    for src in SOURCES:
        seen = set()
        for f in sorted((scraper.DATA / "ads" / src).glob("*/*.jsonl.gz")):
            try:
                with gzip.open(f, "rt", encoding="utf-8") as fh:
                    for line in fh:
                        a = json.loads(line)
                        if (a["id"], a["t"]) in seen:  # the bot and the backfill can both hold a sighting
                            continue
                        seen.add((a["id"], a["t"]))
                        for side in ("give", "get"):
                            for name, kind in {(names.get(scraper.item_key(x.partition("|")[0])), kind_of(x.partition("|")[2]))
                                               for x in a[side]}:
                                if name:
                                    counts[src, a["t"][:10], side, name, kind] += 1
            except (EOFError, OSError, json.JSONDecodeError):
                pass  # a backfill file that is still being written: keep the lines read so far
    df = pd.DataFrame([(*k, n) for k, n in counts.items()], columns=["src", "day", "side", "name", "kind", "n"])
    df["day"] = pd.to_datetime(df.day)
    return df


def log_share(counts, window):
    """log of each column's share of all mentions in the last `window` days; NaN where the window has too few ads."""
    c = counts.rolling(window, min_periods=1).sum()
    total = c.sum(axis=1)
    share = np.log((c + SMOOTH).div(total + SMOOTH * c.shape[1], axis=0))
    return share.where(total >= MIN_MENTIONS)


def ad_features(days, pet_names):
    """Long table (day, name, kind) of ad features for the given days and pets.

    Per source (elve_*, amvgg_*):
      want_7 / offer_7   log share of "wanted" / "offered" ad mentions the pet holds, last 7 days
      demand_7           want_7 - offer_7: above 0 = asked for more than it is offered
      demand_chg         demand_7 minus the same over 30 days: demand rising or cooling
      kind_demand_14     demand for this exact kind (default / neon / mega), last 14 days
    """
    names = {scraper.item_key(n): n for n in pet_names}
    M = mentions(names)
    kinds = ["default", "neon", "mega"]
    pet_cols = pd.Index(sorted(pet_names), name="name")
    kind_cols = pd.MultiIndex.from_product([sorted(pet_names), kinds], names=["name", "kind"])
    pet_level, kind_level = {}, {}
    for src in SOURCES:
        m = M[M.src == src]
        if m.empty:
            continue
        def wide(side, by, cols):
            w = m[m.side == side].groupby(["day"] + by).n.sum().unstack(by).reindex(index=days, columns=cols).fillna(0)
            # no ads at all before the source's first day: keep those days empty instead of "zero demand"
            w.loc[w.index < m.day.min()] = np.nan
            return w
        get, give = wide("get", ["name"], pet_cols), wide("give", ["name"], pet_cols)
        want7, offer7 = log_share(get, 7), log_share(give, 7)
        pet_level[f"{src}_want_7"], pet_level[f"{src}_offer_7"] = want7, offer7
        pet_level[f"{src}_demand_7"] = want7 - offer7
        pet_level[f"{src}_demand_chg"] = (want7 - offer7) - (log_share(get, 30) - log_share(give, 30))
        kind_level[f"{src}_kind_demand_14"] = (log_share(wide("get", ["name", "kind"], kind_cols), 14)
                                               - log_share(wide("give", ["name", "kind"], kind_cols), 14))
    P = pd.concat({k: v.stack(future_stack=True) for k, v in pet_level.items()}, axis=1).rename_axis(["day", "name"]).reset_index()
    K = pd.concat({k: v.stack(["name", "kind"], future_stack=True) for k, v in kind_level.items()}, axis=1) \
        .rename_axis(["day", "name", "kind"]).reset_index()
    return K.merge(P, on=["day", "name"], how="left")


if __name__ == "__main__":  # quick look: coverage and the most / least wanted pets right now
    import elve_model
    log, _ = elve_model.contiguous_log()
    V, _, _ = elve_model.daily_values(log)
    A = ad_features(V.index, sorted(set(V.columns.get_level_values("name"))))
    feats = [c for c in A.columns if c not in ("day", "name", "kind")]
    print(A.groupby("day")[feats].apply(lambda g: g.notna().mean()).resample("QS").mean().round(2).to_string())
    last = A[(A.day == A.day.max()) & (A.kind == "default")].set_index("name")
    for src in SOURCES:
        col = f"{src}_demand_7"
        if col in last and last[col].notna().any():
            s = last[col].sort_values()
            print(f"\n{src}: most wanted vs offered:", ", ".join(s.index[-8:][::-1]), "\n   most offered vs wanted:", ", ".join(s.index[:8]))
