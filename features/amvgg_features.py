"""AMVGG value moves as features: has AMVGG already repriced a pet that Elvebredd hasn't moved yet?

    from features.amvgg_features import amvgg_features
    G = amvgg_features(days, names)   # long table: day, name, kind + feature columns, to merge into the model panel

AMVGG's change log starts 2026-06-02 and only covers fly ride values (Regular / Neon / Mega). Those map to the model's
kinds default / neon / mega. The model's default variant is *no potion*, so for default pets this is the same pet with
a different potion: a related signal, not the same number.
A feature for day t only uses changes logged up to the end of day t (UTC). Everything is empty until the log is 30 days
old, so "no history yet" is never read as "no change".
"""
import gzip
import json

import numpy as np
import pandas as pd

import scraper

KINDS = {"Regular": "default", "Neon": "neon", "Mega": "mega"}
SNAP = {"default": "regularValue", "neon": "neonValue", "mega": "megaValue"}
WARMUP = 30


def amvgg_daily(days, pet_names):
    """Wide matrix (days x (name, kind)) of AMVGG's fly ride value at the end of each day; NaN before the log starts."""
    names = {scraper.item_key(n): n for n in pet_names}
    log = scraper.load_amvgg_updates().drop_duplicates(["id", "variant"])
    log = log[log.variant.isin(KINDS) & log.newValue.notna()]
    log = log.assign(name=log.name.map(lambda n: names.get(scraper.item_key(n))), kind=log.variant.map(KINDS),
                     day=log.updatedAt.dt.tz_convert(None).dt.normalize()).dropna(subset=["name"])
    cols = pd.MultiIndex.from_product([sorted(pet_names), list(SNAP)], names=["name", "kind"])
    days = pd.DatetimeIndex(days)

    f = sorted((scraper.DATA / "values" / "amvgg").glob("*.json.gz"))[-1]
    now = {(names[k], kind): float(i[col]) for i in json.loads(gzip.decompress(f.read_bytes()))
           if i.get("kind", "pets") == "pets" and (k := scraper.item_key(i["name"])) in names
           for kind, col in SNAP.items() if i.get(col) not in (None, "")}
    by = log.groupby(["name", "kind"])
    first = by.previousValue.first().reindex(cols)  # value before the first logged change
    start = first.where(by.size().reindex(cols).notna(), pd.Series(now).reindex(cols))  # never changed: today's value
    start = start.where(start > 0)

    end = log.groupby(["day", "name", "kind"]).newValue.last().unstack(["name", "kind"]).reindex(index=days, columns=cols)
    begin = log.day.min()
    V = end.copy()
    if begin in V.index:
        V.loc[begin] = V.loc[begin].fillna(start)
    V = V.where(V > 0).ffill()
    V.loc[V.index < begin] = np.nan
    return V, begin


def amvgg_features(days, pet_names):
    """Long table (day, name, kind):

      gg_ret_7 / gg_ret_30       log change of AMVGG's value over the last 7 / 30 days
      gg_last_change             size of AMVGG's last change (log), empty if it never changed
      gg_days_since_change       days since AMVGG last changed the value (capped at 60)
      gg_n_up_30 / gg_n_dn_30    AMVGG rises / drops in the last 30 days

    elve_model.add_groups adds gg_lead_7 / gg_lead_30 = AMVGG's change minus Elvebredd's over the same days.
    """
    V, begin = amvgg_daily(days, pet_names)
    L = np.log(V)
    r1 = L.diff()
    up, dn = (r1 > 1e-9).astype(float), (r1 < -1e-9).astype(float)
    idx = pd.DataFrame(np.arange(len(V))[:, None] * np.ones(V.shape[1]), index=V.index, columns=V.columns)
    last = idx.where((up + dn) > 0).ffill()
    feats = {"gg_ret_7": L - L.shift(7), "gg_ret_30": L - L.shift(30),
             "gg_last_change": r1.where((up + dn) > 0).ffill(),
             "gg_days_since_change": (idx - last).clip(upper=60).fillna(60),  # never changed = the cap
             "gg_n_up_30": up.rolling(30, min_periods=1).sum(), "gg_n_dn_30": dn.rolling(30, min_periods=1).sum()}
    ready = (V.index >= begin + pd.Timedelta(days=WARMUP))[:, None] & V.notna().values
    out = pd.concat({k: v.where(ready).stack(["name", "kind"], future_stack=True) for k, v in feats.items()}, axis=1)
    return out.rename_axis(["day", "name", "kind"]).reset_index()


if __name__ == "__main__":  # quick look: coverage, and where AMVGG and Elvebredd disagree most right now
    import elve_model
    log, _ = elve_model.contiguous_log()
    V, _, _ = elve_model.daily_values(log)
    G = amvgg_features(V.index, sorted(set(V.columns.get_level_values("name"))))
    feats = [c for c in G.columns if c not in ("day", "name", "kind")]
    print(G.groupby("day")[feats].apply(lambda g: g.notna().mean()).resample("MS").mean().round(2).tail(7).to_string())
    last = G[G.day == G.day.max()].dropna(subset=["gg_ret_30"]).sort_values("gg_ret_30")
    print("\nAMVGG's biggest 30-day drops:\n", last.head(8)[["name", "kind", "gg_ret_30"]].to_string(index=False))
    print("\nAMVGG's biggest 30-day rises:\n", last.tail(8)[["name", "kind", "gg_ret_30"]].to_string(index=False))
