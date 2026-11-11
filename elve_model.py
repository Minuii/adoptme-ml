"""Elve-only model: predict whether Elvebredd moves a pet variant's value up / flat / down over the next H days,
using only Elvebredd's own change log (no AMVGG, no trades yet).

    python elve_model.py            # build the panel, run the walk-forward test, write results/elve_model.md

Steps:
  1. Daily value of every pet variant (6 per pet: default/neon/mega x no potion/fly ride), rebuilt from the change log.
     Only the newest unbroken run of update batches is used, so backfill gaps can't fake "no change" periods.
  2. Features at the end of day t, from data up to t only (own momentum, other variants of the same pet, rarity and market activity).
  3. Target: log change from end of day t to end of day t+H, as down / flat / up (|change| < FLAT counts as flat).
  4. Walk-forward by month: train on everything that ends before the test month (gap of H days), test on that month.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import scraper

H = 7               # horizon in days
FLAT = np.log(1.02)  # moves under 2% count as flat
WARMUP = 30          # days of history needed before a row is used
TOP_K = 20           # picks per day in the trading simulation
LABELS = {"default no potion": "rvalue - nopotion", "default fly ride": "rvalue - fly&ride",
          "neon no potion": "nvalue - nopotion", "neon fly ride": "nvalue - fly&ride",
          "mega no potion": "mvalue - nopotion", "mega fly ride": "mvalue - fly&ride"}
# Elve logs these three reliably (~90% of rebuilt values match today's snapshot). The other three (~76%) often change
# without a log entry, so they only feed the pet-level features and are never predicted.
MAIN = ["default no potion", "neon fly ride", "mega fly ride"]
OUT = Path("results")


def contiguous_log():
    """Pet changes from the newest unbroken run of batches (the backfill runs newest-first, so older gaps get cut off)."""
    df = scraper.load_elve_updates()
    batches = sorted(set(df.batch) | {scraper.json.loads(l)["batch"] for l in
                                      (scraper.DATA / "elve_updates" / "empty.jsonl").read_text(encoding="utf-8").splitlines()})
    first = batches[-1]
    for b in reversed(batches):
        if b != first and b != first - 1:
            break
        first = b
    df = df[(df.batch >= first) & (df.itemType == "pets") & df.label.isin(LABELS)]
    return df, first


def daily_values(log):
    """Wide matrix: rows = days, columns = (pet, variant), value at end of day. NaN before a pet's release."""
    snap = scraper.load_values("elve")
    snap = snap[(snap.scraped_at == snap.scraped_at.max()) & (snap.type == "pets")]
    today = snap[["name"] + list(LABELS.values())].melt(id_vars=["name"], value_vars=list(LABELS.values()), var_name="col", value_name="val")
    today["label"] = today.col.map({v: k for k, v in LABELS.items()})
    rarity = dict(zip(snap.name, snap.rarity))

    log = log.assign(day=log.effectiveAt.dt.tz_convert(None).dt.normalize())
    days = pd.date_range(log.day.min(), log.day.max() - pd.Timedelta(days=1))  # the last day may be incomplete
    log = log[log.day <= days[-1]]
    pairs = sorted(set(zip(today.name, today.label)) | set(zip(log.name, log.label)))
    cols = pd.MultiIndex.from_tuples(pairs, names=["name", "label"])

    end = log.groupby(["day", "name", "label"]).newValue.last().unstack(["name", "label"]).reindex(index=days, columns=cols)
    first = log.groupby(["name", "label"]).previousValue.first().reindex(cols)  # value before the first logged change
    now = today.set_index(["name", "label"]).val.reindex(cols)
    start = first.where(first.notna(), now.where(log.groupby(["name", "label"]).size().reindex(cols).isna()))
    start = start.where(start > 0)  # previousValue 0 = pet released inside the window
    V = end.copy()
    V.iloc[0] = V.iloc[0].fillna(start)
    V = V.ffill()
    nchg = log.groupby(["day", "name", "label"]).size().unstack(["name", "label"]).reindex(index=days, columns=cols).fillna(0)
    return V, nchg, rarity


def features(V, nchg, rarity):
    """Long table: one row per (day, pet variant) with features and the H-day target."""
    L = np.log(V.where(V > 0))
    r1 = L.diff()  # daily log change
    up, dn = (r1 > 1e-9).astype(float), (r1 < -1e-9).astype(float)
    changed = (nchg > 0) | (up + dn > 0)

    idx = np.arange(len(V))[:, None] * np.ones(V.shape[1])
    last = pd.DataFrame(np.where(changed, idx, np.nan), index=V.index, columns=V.columns).ffill()
    born = V.notna().cumsum()
    lastchg = r1.where(changed).ffill()

    pet = V.columns.get_level_values("name")
    def by_pet(M):  # sum over the pet's other variants
        return M.T.groupby(pet).transform("sum").T - M
    def roll(M, n):
        return M.rolling(n, min_periods=1).sum()

    rar = pd.Series([rarity.get(n, "unknown") for n in pet], index=V.columns)
    def by_rarity_share(n):  # share of moves that were up in the pet's rarity, last n days
        u, d = roll(up, n), roll(dn, n)
        su = u.T.groupby(rar.values).transform("sum").T
        sd = d.T.groupby(rar.values).transform("sum").T
        return su / (su + sd).replace(0, np.nan)

    mkt_moves = changed.sum(axis=1)
    mkt_up7 = roll(up, 7).sum(axis=1) / (roll(up, 7) + roll(dn, 7)).sum(axis=1).replace(0, np.nan)

    F = {
        "log_value": L,
        "ret_1": r1, "ret_7": L - L.shift(7), "ret_30": L - L.shift(30), "ret_90": L - L.shift(90),
        "n_up_30": roll(up, 30), "n_dn_30": roll(dn, 30), "n_up_90": roll(up, 90), "n_dn_90": roll(dn, 90),
        "days_since_change": pd.DataFrame(idx, index=V.index, columns=V.columns) - last,
        "last_change": lastchg,
        "age_days": born,
        "pet_up_3": by_pet(roll(up, 3)), "pet_dn_3": by_pet(roll(dn, 3)),
        "pet_up_14": by_pet(roll(up, 14)), "pet_dn_14": by_pet(roll(dn, 14)),
        "rarity_up_share_7": by_rarity_share(7), "rarity_up_share_30": by_rarity_share(30),
        "target": L.shift(-H) - L,
    }
    df = pd.concat({k: v.stack(["name", "label"], future_stack=True) for k, v in F.items()}, axis=1)
    df.index.names = ["day", "name", "label"]
    df = df.reset_index()
    df["mkt_moves_1"] = df.day.map(mkt_moves)
    df["mkt_moves_7"] = df.day.map(mkt_moves.rolling(7, min_periods=1).sum())
    df["mkt_up_share_7"] = df.day.map(mkt_up7)
    df["rarity"] = df.name.map(rarity).fillna("unknown")
    df["kind"] = df.label.str.split().str[0]
    df["no_potion"] = df.label.str.endswith("no potion").astype(int)
    df["dow"] = df.day.dt.dayofweek
    for c in ("rarity", "kind"):
        df = pd.concat([df, pd.get_dummies(df[c], prefix=c, dtype=float)], axis=1)
    df = df[df.log_value.notna() & (df.day >= V.index[0] + pd.Timedelta(days=WARMUP)) & df.label.isin(MAIN)]
    df["y"] = np.select([df.target > FLAT, df.target < -FLAT], [2, 0], 1)  # 0 down, 1 flat, 2 up
    df.loc[df.target.isna(), "y"] = -1  # future unknown (last H days)
    return df


def baselines(test):
    flat = np.tile([0, 1, 0], (len(test), 1)).astype(float)
    # repeat the last change's direction if it happened in the last 30 days, else flat
    rep = np.where(test.days_since_change <= 30, np.sign(test.last_change.fillna(0)) + 1, 1).astype(int)
    return {"always flat": flat, "repeat last change (30d)": np.eye(3)[rep]}


def scores(y, P, test):
    from sklearn.metrics import f1_score, log_loss
    pred = P.argmax(1)
    out = {"accuracy": (pred == y).mean(), "macro F1": f1_score(y, pred, average="macro"),
           "up precision": ((pred == 2) & (y == 2)).sum() / max((pred == 2).sum(), 1),
           "up recall": ((pred == 2) & (y == 2)).sum() / max((y == 2).sum(), 1),
           "down precision": ((pred == 0) & (y == 0)).sum() / max((pred == 0).sum(), 1),
           "down recall": ((pred == 0) & (y == 0)).sum() / max((y == 0).sum(), 1)}
    soft = np.clip(P, 1e-3, 1)
    out["log loss"] = log_loss(y, soft / soft.sum(1, keepdims=True), labels=[0, 1, 2])
    # trading sim: each day hold the TOP_K variants with the highest P(up) - P(down); score = their mean H-day change
    t = test.assign(s=P[:, 2] - P[:, 0] + 1e-6 * np.random.default_rng(0).random(len(test)))
    picks = t[t.s > 0].sort_values("s", ascending=False).groupby("day").head(TOP_K)
    out[f"top-{TOP_K} mean {H}d change"] = np.expm1(picks.target).mean() if len(picks) else np.nan
    out["universe mean change"] = np.expm1(test.target).mean()
    return out


def walk_forward(df):
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    feats = [c for c in df.columns if c not in ("day", "name", "label", "target", "y", "rarity", "kind")]
    data = df[df.y >= 0]
    months = sorted(data.day.dt.to_period("M").unique())
    test_months = [m for m in months if (data.day.dt.to_period("M") < m).sum() > 0][2:]  # at least ~3 months of training
    rows, imp = [], None
    for m in test_months:
        test = data[data.day.dt.to_period("M") == m]
        train = data[data.day < test.day.min() - pd.Timedelta(days=H)]
        Xtr, Xte = train[feats].fillna(0).values, test[feats].fillna(0).values
        models = {
            "logistic regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=300, C=0.5)),
            "gradient boosting": HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                                                l2_regularization=1.0, random_state=0),
        }
        preds = baselines(test)
        for name, mdl in models.items():
            mdl.fit(Xtr, train.y.values)
            preds[name] = mdl.predict_proba(Xte)
        for name, P in preds.items():
            rows.append(dict(month=str(m), model=name, n_test=len(test), **scores(test.y.values, P, test)))
        print(f"{m}: train {len(train):,} rows, test {len(test):,}", flush=True)
        imp = (models["logistic regression"][-1].coef_, feats)
    return pd.DataFrame(rows), imp


def main():
    log, first_batch = contiguous_log()
    V, nchg, rarity = daily_values(log)
    df = features(V, nchg, rarity)
    lab = df[df.y >= 0].y.value_counts(normalize=True).sort_index()
    print(f"window {V.index[0].date()} -> {V.index[-1].date()} (batches {first_batch}+), {V.shape[1]} pet variants, "
          f"{len(df):,} rows; down/flat/up = {lab.round(3).tolist()}", flush=True)
    res, (coef, feats) = walk_forward(df)

    OUT.mkdir(exist_ok=True)
    res.to_csv(OUT / "elve_model_folds.csv", index=False)
    summ = res.drop(columns=["month", "n_test"]).groupby("model", sort=False).mean()
    upcoef = pd.Series(coef[2] - coef[0], index=feats).sort_values()
    md = [f"# Elve-only model: {H}-day up/flat/down\n",
          f"_Window {V.index[0].date()} to {V.index[-1].date()}, {V.shape[1]:,} pet variants, {len(df):,} rows. "
          f"Flat = move under {np.expm1(FLAT):.0%}. Class shares down/flat/up: {', '.join(f'{x:.1%}' for x in lab)}._\n",
          f"Walk-forward by month ({res.month.nunique()} test months), averages:\n",
          summ.to_markdown(floatfmt=".3f"), "\n\n## Per month\n",
          res.pivot(index="month", columns="model", values="macro F1").to_markdown(floatfmt=".3f"),
          "\n\n## Logistic regression: features pushing toward up (+) or down (-), last fold\n",
          pd.concat([upcoef.head(8), upcoef.tail(8)]).to_frame("up minus down coef").to_markdown(floatfmt=".3f")]
    (OUT / "elve_model.md").write_text("\n".join(md), encoding="utf-8")
    print(summ.round(3).to_string())


if __name__ == "__main__":
    main()
