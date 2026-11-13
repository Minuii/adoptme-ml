"""Elve-only model: predict whether Elvebredd moves a pet variant's value up / flat / down over the next H days,
using only Elvebredd's own change log (no AMVGG, no trades yet).

    python elve_model.py            # build the panel, run the walk-forward test, write results/elve_model.md
    python elve_model.py ads        # same test on the months that have offers (trade listings), with and without the offer features
                                    # (ad_features.py) -> results/ads_model.md
    python elve_model.py ads 3      # only the last 3 test months (quick check)
    python elve_model.py events [N] # same, with and without game-update features from playadopt.me/news
                                    # (event_features.py) -> results/events_model.md
    python elve_model.py both [N]   # offer months only: base, + offers, + events, + both -> results/both_model.md
                                    # (H=30 python elve_model.py both -> results/both_model_30d.md)
    python elve_model.py amvgg [N]  # months with AMVGG's own change log (2026-07 on): base vs + AMVGG value moves
                                    # (amvgg_features.py), plus the "AMVGG moved first" rule as a baseline -> results/amvgg_model.md
    python elve_model.py size [N]   # how much, not just which way: expected % change + 10-90% range (offers + news),
                                    # tested walk-forward -> results/size_model.md, plus results/forecast.csv for today
    python elve_model.py forecast   # no test: train the offers + news classifier on every row with a known outcome and call
                                    # the newest day up / flat / down -> results/direction_<H>d.csv (the site shows it;
                                    # the daily forecast workflow runs H=30), and keeps a copy in results/forecast_log/<H>d/<day>.csv.gz
                                    # for the live track record (track_record.py). ~10 min, ~5 GB RAM.

Only pets that AMVGG also lists (802) are modelled. AMVGG's value moves are tested in `amvgg` mode only (short history);
trades are not features yet.

Steps:
  1. Daily value of every pet variant (6 per pet: default/neon/mega x no potion/fly ride), rebuilt from the change log.
     Only the newest unbroken run of update batches is used, so backfill gaps can't fake "no change" periods.
  2. Features at the end of day t, from data up to t only (own momentum, other variants of the same pet, rarity and market activity).
  3. Target: log change from end of day t to end of day t+H, as down / flat / up (|change| < FLAT counts as flat).
  4. Walk-forward by month: train on everything that ends before the test month (gap of H days), test on that month.
"""
import gzip
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import scraper

H = int(os.environ.get("H", 7))  # horizon in days; H=30 python elve_model.py events -> results/events_model_30d.md
# moves under this count as flat; wider for longer horizons (2% / 5% / 10% at 7 / 30 / 90 days), override with FLAT=0.03
FLAT = np.log1p(float(os.environ.get("FLAT", 0.02 if H <= 7 else 0.05 if H <= 30 else 0.10)))
SUFFIX = "" if H == 7 else f"_{H}d"
WARMUP = 30          # days of history needed before a row is used
TOP_K = 20           # picks per day in the trading simulation
AGE_CAP = 365        # age_days stops counting here; pets older than the window start at the cap (their real age is unknown)
# A quarter of default no-potion values are under 0.1, where one step of Elve's list is a 25%+ move. The picks are also
# scored on pets worth at least this much, so a result can't rest on penny pets alone. Override with VALUE_FLOOR=1.
VALUE_FLOOR = float(os.environ.get("VALUE_FLOOR", 0.25))
RECALL_AT = 0.30     # "precision at 30% recall": how often the model is right when asked to catch 3 in 10 moves
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


def amvgg_pet_keys():
    """item_key of every pet on AMVGG's list: the model's universe (the same 802 pets on both sites)."""
    f = sorted((scraper.DATA / "values" / "amvgg").glob("*.json.gz"))[-1]
    return {scraper.item_key(i["name"]) for i in json.loads(gzip.decompress(f.read_bytes())) if i.get("kind", "pets") == "pets"}


def daily_values(log):
    """Wide matrix: rows = days, columns = (pet, variant), value at end of day. NaN before a pet's release."""
    snap = scraper.load_values("elve")
    snap = snap[(snap.scraped_at == snap.scraped_at.max()) & (snap.type == "pets")]
    # Elvebredd lists some pets twice (e.g. "Skele-Rex" / "Skele-rex"); keep the entry the log follows, under one name
    keep = amvgg_pet_keys()
    canon = {i["id"]: i["name"] for k, i in scraper.elve_canonical(snap.to_dict("records"), log.to_dict("records")).items() if k in keep}
    log = log[log.petId.isin(canon)]
    snap = snap[snap.id.isin(canon)]
    log = log.assign(name=log.petId.map(canon).fillna(log.name))
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
    # Days since the pet first had a value, capped. Pets that already existed on the window's first day would otherwise
    # all count up from that day together (a calendar clock the trees can read the period from), so they sit at the cap.
    born = V.notna().cumsum().clip(upper=AGE_CAP)
    born.loc[:, V.iloc[0].notna().values] = AGE_CAP
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
    df["dow"] = df.day.dt.day_of_week
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
    out = {"always flat": flat, "repeat last change (30d)": np.eye(3)[rep]}
    if "gg_lead_30" in test:  # the project's first idea: AMVGG moves first, Elvebredd follows
        lead = test.gg_lead_30.fillna(0).values
        out["AMVGG moved first (30d gap)"] = np.eye(3)[np.select([lead > FLAT, lead < -FLAT], [2, 0], 1)]
    return out


def pick_stats(test, score, jitter=1e-9):
    """Trading sim: each day hold the TOP_K variants with the highest score (only scores above 0); result = their H-day
    change. Besides the plain mean: the median, the same on pets worth at least VALUE_FLOOR, one kind at a time, and with
    new picks only every H days (counted from the test month's first day). Daily picks are held H days, so they overlap and one good call is counted up to H times;
    the every-H-days version counts each bet once."""
    score = np.asarray(score, dtype=float)
    # the jitter only breaks ties between real picks: a score of exactly 0 ("flat") must never become a random pick
    t = test.assign(s=score + jitter * np.random.default_rng(0).random(len(test)))[score > 0]

    def top(d):
        return np.expm1(d.sort_values("s", ascending=False).groupby("day").head(TOP_K).target)
    picks = top(t)
    out = {f"top-{TOP_K} mean {H}d change": picks.mean(), f"top-{TOP_K} median": picks.median(),
           f"top-{TOP_K}, new picks every {H}d": top(t[(t.day - test.day.min()).dt.days % H == 0]).mean(),
           f"top-{TOP_K}, value >= {VALUE_FLOOR:g}": top(t[t.log_value >= np.log(VALUE_FLOOR)]).mean()}
    for kind in ("default", "neon", "mega"):
        out[f"top-{TOP_K}, {kind} only"] = top(t[t.kind == kind]).mean()
    return out


def scores(y, P, test):
    from sklearn.metrics import average_precision_score, f1_score, log_loss, precision_recall_curve
    pred = P.argmax(1)
    out = {"accuracy": (pred == y).mean(), "macro F1": f1_score(y, pred, average="macro"),
           "up precision": ((pred == 2) & (y == 2)).sum() / max((pred == 2).sum(), 1),
           "up recall": ((pred == 2) & (y == 2)).sum() / max((y == 2).sum(), 1),
           "down precision": ((pred == 0) & (y == 0)).sum() / max((pred == 0).sum(), 1),
           "down recall": ((pred == 0) & (y == 0)).sum() / max((y == 0).sum(), 1)}
    soft = np.clip(P, 1e-3, 1)
    out["log loss"] = log_loss(y, soft / soft.sum(1, keepdims=True), labels=[0, 1, 2])
    # The numbers above take the likeliest class, and most rows are flat, so few moves get called. These two don't
    # depend on that cut-off: they rank rows by P(up) / P(down).
    for side, cls in (("up", 2), ("down", 0)):
        pos = y == cls
        ap = prec = np.nan
        if pos.any() and not pos.all():
            ap = average_precision_score(pos, P[:, cls])
            pr, rc, _ = precision_recall_curve(pos, P[:, cls])
            prec = pr[rc >= RECALL_AT].max()
        out[f"{side} avg precision"], out[f"{side} precision @{RECALL_AT:.0%} recall"] = ap, prec
    out.update(pick_stats(test, P[:, 2] - P[:, 0], 1e-6))
    out["universe mean change"] = np.expm1(test.target).mean()
    return out


def boot_table(res, cols, n=2000):
    """Mean over test months with a 90% range from resampling the months (each month is one draw), and the share of
    months in which the picks beat the average pet."""
    rng, rows = np.random.default_rng(0), []
    for model, g in res.groupby("model", sort=False):
        for c in cols:
            ok = g[c].notna()
            x = g.loc[ok, c].values
            if len(x) < 2:
                continue
            m = rng.choice(x, (n, len(x))).mean(1)
            row = {"model": model, "picks": c, "months": len(x), "mean": x.mean(), "5%": np.quantile(m, .05), "95%": np.quantile(m, .95)}
            if "universe mean change" in g:
                row["months beating all pets"] = (x > g.loc[ok, "universe mean change"].values).mean()
            rows.append(row)
    return pd.DataFrame(rows)


def tables(res, summ):
    """Markdown for a results file: the picks table (each row = one model) and the month-resampled ranges."""
    pick_cols = [c for c in summ.columns if c.startswith("top-")]
    md = ["\n\n## Top-20 picks: how solid is the gain\n",
          f"Mean {H}-day change of the picks. *new picks every {H}d* counts each bet once (daily picks are held {H} days and "
          f"overlap); *value >= {VALUE_FLOOR:g}* leaves out penny pets, where one step of the list is a huge % move.\n",
          summ[pick_cols + [c for c in ("universe mean change",) if c in summ]].to_markdown(floatfmt=".3f")]
    boot = boot_table(res, pick_cols[:1] + [c for c in pick_cols if "new picks" in c])
    if len(boot):
        md += ["\n\n### Range over months (90%, months resampled 2,000 times)\n", boot.to_markdown(index=False, floatfmt=".3f")]
    return md, pick_cols


NOT_FEATURES = ("day", "name", "label", "target", "y", "rarity", "kind")


def varying(train, feats):
    """Drop columns with under 2 distinct values in the training rows: they carry nothing, and scikit-learn's
    histogram boosting crashes on them ("window shape cannot be larger than input array shape")."""
    keep = [c for c in feats if train[c].nunique() > 1]
    if len(keep) < len(feats):
        print("  constant in training, dropped:", ", ".join(c for c in feats if c not in keep), flush=True)
    return keep


def walk_forward(df, feature_sets=None, last=None):
    """feature_sets: {suffix: feature columns}; every set gets a logistic regression and a gradient boosting model,
    all tested on the same rows. last: only the newest N test months."""
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    boosting = _classifier  # XGBoost on a GPU machine (Kaggle), scikit-learn otherwise; same shape of model
    print("gradient boosting:", type(boosting()).__name__, flush=True)

    feature_sets = feature_sets or {"": [c for c in df.columns if c not in NOT_FEATURES]}
    data = df[df.y >= 0]
    months = sorted(data.day.dt.to_period("M").unique())
    # a month is tested only if its training rows (everything up to H days before it) span at least ~2 months;
    # for H=7 that is the same months as before, for H=90 the first ~4 months are skipped instead of training on nothing
    test_months = [m for m in months if m.start_time - pd.Timedelta(days=H) - data.day.min() >= pd.Timedelta(days=50)]
    rows, imp = [], None
    for m in test_months[-last:] if last else test_months:
        test = data[data.day.dt.to_period("M") == m]
        train = data[data.day < test.day.min() - pd.Timedelta(days=H)]
        preds = baselines(test)
        for suffix, feats in feature_sets.items():
            feats = varying(train, feats)
            Xtr, Xte = train[feats], test[feats]
            models = {
                # the linear model can't take gaps (offer features are empty before a site's offers begin): 0 = "average"
                "logistic regression": (make_pipeline(StandardScaler(), LogisticRegression(max_iter=300, C=0.5)), True),
                # boosting handles missing values itself, so "no ad data" stays distinct from "zero demand"
                "gradient boosting": (boosting(), False),
            }
            for name, (mdl, fill) in models.items():
                mdl.fit(Xtr.fillna(0).values if fill else Xtr.values, train.y.values)
                preds[name + suffix] = mdl.predict_proba(Xte.fillna(0).values if fill else Xte.values)
            imp = (models["logistic regression"][0][-1].coef_, feats)
        for name, P in preds.items():
            rows.append(dict(month=str(m), model=name, n_test=len(test), **scores(test.y.values, P, test)))
        print(f"{m}: train {len(train):,} rows, test {len(test):,}", flush=True)
    return pd.DataFrame(rows), imp


def add_groups(df, V, groups):
    """Merge extra feature groups ("offers", "events") and keep only days where every group exists."""
    pets = sorted(set(V.columns.get_level_values("name")))
    cols, start = {}, df.day.min()
    for g in groups:
        if g == "offers":
            from ad_features import ad_features
            X, on = ad_features(V.index, pets), ["day", "name", "kind"]
        elif g == "amvgg":
            from amvgg_features import amvgg_features
            X, on = amvgg_features(V.index, pets), ["day", "name", "kind"]
        else:
            from event_features import event_features
            X, on = event_features(V.index, pets), ["day", "name"]
        cols[g] = [c for c in X.columns if c not in ("day", "name", "kind")]
        df = df.merge(X, on=on, how="left")
        start = max(start, X.loc[X[cols[g]].notna().any(axis=1), "day"].min())  # first day this group exists
        if g == "amvgg":  # how far AMVGG has moved ahead of Elvebredd: above 0 = AMVGG rose more (or fell less)
            df["gg_lead_7"], df["gg_lead_30"] = df.gg_ret_7 - df.ret_7, df.gg_ret_30 - df.ret_30
            cols[g] += ["gg_lead_7", "gg_lead_30"]
    df = df[df.day >= start]
    print(f"{'+'.join(groups)} features from {start.date()}: {len(df):,} rows, coverage "
          + ", ".join(f"{c} {df[c].notna().mean():.0%}" for cs in cols.values() for c in cs), flush=True)
    return df, cols


# ---- size model: how much, not just which way -------------------------------------------------------------------
QUANTILES = (0.1, 0.5, 0.9)  # the range shown is the 10%-90% band: about 8 in 10 outcomes should land inside it


def _gpu():
    import shutil
    if not shutil.which("nvidia-smi"):
        return False
    try:
        import xgboost  # noqa: F401
        return True
    except ImportError:
        return False


def _classifier():
    if _gpu():
        from xgboost import XGBClassifier
        return XGBClassifier(device="cuda", tree_method="hist", n_estimators=300, learning_rate=0.05, max_leaves=31,
                             grow_policy="lossguide", reg_lambda=1.0, random_state=0)
    from sklearn.ensemble import HistGradientBoostingClassifier
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31, l2_regularization=1.0, random_state=0)


def _regressor(loss="squared_error", q=None):
    """Boosted regressor on the log change; loss "quantile" with q = the quantile."""
    if _gpu():
        from xgboost import XGBRegressor
        kw = dict(objective="reg:quantileerror", quantile_alpha=q) if loss == "quantile" else dict(objective="reg:squarederror")
        return XGBRegressor(device="cuda", tree_method="hist", n_estimators=300, learning_rate=0.05, max_leaves=31,
                            grow_policy="lossguide", reg_lambda=1.0, random_state=0, **kw)
    from sklearn.ensemble import HistGradientBoostingRegressor
    kw = dict(loss="quantile", quantile=q) if loss == "quantile" else dict(loss="squared_error")
    return HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=31, l2_regularization=1.0,
                                         random_state=0, **kw)


def fit_size(train, feats):
    """Two-part model. 1) classifier: P(down / flat / up). 2) regressors trained only on rows that moved: typical size of
    a rise and of a drop. Expected change = P(up) x rise + P(down) x drop + P(flat) x (mean flat drift), in % terms.
    Also quantile regressors on the raw log change for the 10/50/90% range."""
    X, y, t = train[feats].values, train.y.values, train.target.values
    m = {"clf": _classifier().fit(X, y)}
    for k, cls in (("up", 2), ("down", 0)):
        sel = y == cls
        m[k] = _regressor().fit(X[sel], t[sel])
    m["flat"] = float(np.expm1(t[y == 1]).mean())
    m["direct"] = _regressor().fit(X, t)  # one regressor on everything, to show why the two-part model is needed
    m["q"] = [_regressor("quantile", q).fit(X, t) for q in QUANTILES]
    return m


def predict_size(m, test, feats):
    X = test[feats].values
    P = m["clf"].predict_proba(X)
    up = np.maximum(np.expm1(m["up"].predict(X)), np.expm1(FLAT))    # a rise is at least the flat band
    dn = np.minimum(np.expm1(m["down"].predict(X)), np.expm1(-FLAT))
    q = np.sort(np.column_stack([np.expm1(r.predict(X)) for r in m["q"]]), axis=1)  # sorted, so the band never crosses
    return pd.DataFrame({"p_down": P[:, 0], "p_flat": P[:, 1], "p_up": P[:, 2], "rise_if_up": up, "drop_if_down": dn,
                         "expected": P[:, 2] * up + P[:, 0] * dn + P[:, 1] * m["flat"],
                         "direct": np.expm1(m["direct"].predict(X)),
                         **{f"q{int(a * 100)}": q[:, i] for i, a in enumerate(QUANTILES)}}, index=test.index)


def size_scores(test, pred):
    """Errors in % points of value change; rank IC = mean daily Spearman correlation between predicted and real change."""
    actual = np.expm1(test.target)
    moved = test.y != 1
    rep = np.where(test.days_since_change <= 30, np.expm1(test.last_change.fillna(0)), 0.0)
    rows = []
    for name, p in {"no change": np.zeros(len(test)), "repeat last change (30d)": rep,
                    "direct regression": pred.direct.values, "two-part (expected)": pred.expected.values,
                    "median (q50)": pred.q50.values}.items():
        p = pd.Series(p, index=test.index)
        ic = pd.DataFrame({"d": test.day, "p": p, "a": actual}).groupby("d").apply(
            lambda g: g.p.corr(g.a, method="spearman") if g.p.nunique() > 1 and g.a.nunique() > 1 else np.nan)
        rows.append({"model": name, "MAE (pp)": 100 * (p - actual).abs().mean(),
                     "MAE on movers (pp)": 100 * (p - actual)[moved].abs().mean(),
                     "direction right on movers": (np.sign(p[moved]) == np.sign(actual[moved])).mean(),
                     "rank IC": ic.mean(), **pick_stats(test, p), "universe mean change": actual.mean()})
    inside = (actual >= pred.q10) & (actual <= pred.q90)
    band = {"model": "10-90% range", "coverage": inside.mean(), "coverage on movers": inside[moved].mean(),
            "mean width (pp)": 100 * (pred.q90 - pred.q10).mean(), "share of zero-width ranges": ((pred.q90 - pred.q10) < 1e-4).mean()}
    return rows, band


def size_main(df, feats, V, lab, last):
    data = df[df.y >= 0]
    months = sorted(data.day.dt.to_period("M").unique())
    test_months = [m for m in months if m.start_time - pd.Timedelta(days=H) - data.day.min() >= pd.Timedelta(days=50)]
    rows, bands = [], []
    for mo in test_months[-last:] if last else test_months:
        test = data[data.day.dt.to_period("M") == mo]
        train = data[data.day < test.day.min() - pd.Timedelta(days=H)]
        f = varying(train, feats)
        r, b = size_scores(test, predict_size(fit_size(train, f), test, f))
        rows += [dict(month=str(mo), **x) for x in r]
        bands.append(dict(month=str(mo), **b))
        print(f"{mo}: train {len(train):,} rows, test {len(test):,}", flush=True)
    res, band = pd.DataFrame(rows), pd.DataFrame(bands)

    # forecast for the newest day: train on every row whose outcome is known, predict the newest day
    newest = df.day.max()
    now = df[df.day == newest]
    f = varying(data, feats)
    p = predict_size(fit_size(data, f), now, f)
    fc = now[["name", "label"]].assign(value=np.exp(now.log_value)).join(p)
    for c in ("expected", "q10", "q50", "q90"):
        fc[f"value_{c}"] = fc.value * (1 + fc[c])
    fc = fc.sort_values("expected", ascending=False)

    out = f"size_model{SUFFIX}"
    OUT.mkdir(exist_ok=True)
    res.to_csv(OUT / f"{out}_folds.csv", index=False)
    fc.round(4).to_csv(OUT / f"forecast{SUFFIX}.csv", index=False)
    summ = res.drop(columns="month").groupby("model", sort=False).mean()
    pick_md, pick_cols = tables(res, summ)
    bsum = band.drop(columns=["month", "model"]).mean().to_frame("10-90% range")
    show = ["name", "label", "value", "p_up", "p_down", "expected", "q10", "q90"]
    md = [f"# Elve size model (offers + news): expected % change over {H} days, with a 10-90% range\n",
          f"_Window {V.index[0].date()} to {V.index[-1].date()}, {len(df):,} rows (offer months only). "
          f"Flat = move under {np.expm1(FLAT):.0%}. Class shares down/flat/up: {', '.join(f'{x:.1%}' for x in lab)}._\n",
          f"Walk-forward by month ({res.month.nunique()} test months), averages. pp = percentage points of value change.\n",
          summ.drop(columns=pick_cols[1:] + ["universe mean change"]).to_markdown(floatfmt=".3f"), *pick_md,
          "\n\n## Range (10%-90% quantiles)\n",
          "Coverage should be about 0.80. A zero-width range means the model expects no change at all.\n",
          bsum.to_markdown(floatfmt=".3f"), "\n\n## Per month: rank IC\n",
          res.pivot(index="month", columns="model", values="rank IC").to_markdown(floatfmt=".3f"),
          f"\n\n## Forecast from {newest.date()}: top 15 expected rises and drops (full list in forecast{SUFFIX}.csv)\n",
          pd.concat([fc.head(15), fc.tail(15)])[show].to_markdown(index=False, floatfmt=".3f")]
    (OUT / f"{out}.md").write_text("\n".join(md), encoding="utf-8")
    print(summ.round(3).to_string())
    print(bsum.round(3).to_string())


def forecast_main(df, feats, V):
    """Today's direction call per pet variant, for the site. Same model as "gradient boosting + offers + events" in
    both mode (whose walk-forward results are the backtest the site quotes), trained on every row whose H-day outcome is
    already known, i.e. up to H days before the newest day."""
    data = df[df.y >= 0]
    newest = df.day.max()
    now = df[df.day == newest]
    f = varying(data, feats)
    P = _classifier().fit(data[f].values, data.y.values).predict_proba(now[f].values)
    fc = now[["name", "label"]].assign(value=np.exp(now.log_value).round(4), p_down=P[:, 0], p_flat=P[:, 1], p_up=P[:, 2])
    fc["call"] = np.array(["down", "flat", "up"])[P.argmax(1)]
    fc = fc.sort_values("p_up", ascending=False).round(4)
    OUT.mkdir(exist_ok=True)
    path = OUT / f"direction_{H}d.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(f"# as of {newest.date()} (end of day UTC), {H} days ahead, trained on {data.day.min().date()} to "
                 f"{data.day.max().date()}, {len(data):,} rows, {type(_classifier()).__name__}\n")
        fc.to_csv(fh, index=False, lineterminator="\n")
    # keep every day's calls, so they can be scored once their outcome is known (track_record.py, the site's Stats tab)
    log_dir = OUT / "forecast_log" / f"{H}d"
    log_dir.mkdir(parents=True, exist_ok=True)
    fc[["name", "label", "value", "p_down", "p_flat", "p_up", "call"]].to_csv(
        log_dir / f"{newest.date()}.csv.gz", index=False, lineterminator="\n", compression={"method": "gzip", "mtime": 0})
    print(f"{path}: {len(fc)} pet variants as of {newest.date()}; calls:", fc.call.value_counts().to_dict())


def main():
    log, first_batch = contiguous_log()
    V, nchg, rarity = daily_values(log)
    df = features(V, nchg, rarity)
    lab = df[df.y >= 0].y.value_counts(normalize=True).sort_index()
    print(f"window {V.index[0].date()} -> {V.index[-1].date()} (batches {first_batch}+), {V.shape[1]} pet variants, "
          f"{len(df):,} rows; down/flat/up = {lab.round(3).tolist()}", flush=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    out, title = "elve_model", "Elve-only model"
    last = int(sys.argv[2]) if len(sys.argv) > 2 else None
    if mode == "forecast":
        base = [c for c in df.columns if c not in NOT_FEATURES]
        df, cols = add_groups(df, V, ("offers", "events"))
        forecast_main(df, base + [c for cs in cols.values() for c in cs], V)
        return
    if mode == "size":
        base = [c for c in df.columns if c not in NOT_FEATURES]
        df, cols = add_groups(df, V, ("offers", "events"))
        size_main(df, base + [c for cs in cols.values() for c in cs], V, lab, last)
        return
    if mode in ("ads", "events", "both", "amvgg"):  # same test with and without extra feature groups
        base = [c for c in df.columns if c not in NOT_FEATURES]
        groups = {"ads": ("offers",), "events": ("events",), "both": ("offers", "events"), "amvgg": ("amvgg",)}[mode]
        df, cols = add_groups(df, V, groups)
        sets = {"": base, **{f" + {g}": base + cs for g, cs in cols.items()}}
        if len(cols) > 1:
            sets[" + offers + events"] = base + [c for cs in cols.values() for c in cs]
        res, (coef, feats) = walk_forward(df, sets, last)
        label = {"ads": "offer", "events": "game-update (news)", "both": "offer and game-update (news)",
                 "amvgg": "AMVGG value-move"}[mode]
        out, title = f"{mode}_model", f"Elve model with {label} features"
    else:
        res, (coef, feats) = walk_forward(df, last=last)

    out += SUFFIX
    OUT.mkdir(exist_ok=True)
    res.to_csv(OUT / f"{out}_folds.csv", index=False)
    summ = res.drop(columns=["month", "n_test"]).groupby("model", sort=False).mean()
    pick_md, pick_cols = tables(res, summ)
    upcoef = pd.Series(coef[2] - coef[0], index=feats).sort_values()
    md = [f"# {title}: {H}-day up/flat/down\n",
          f"_Window {V.index[0].date()} to {V.index[-1].date()}, {V.shape[1]:,} pet variants, {len(df):,} rows. "
          f"Flat = move under {np.expm1(FLAT):.0%}. Class shares down/flat/up: {', '.join(f'{x:.1%}' for x in lab)}._\n",
          f"Walk-forward by month ({res.month.nunique()} test months), averages:\n",
          summ.drop(columns=pick_cols[1:] + ["universe mean change"]).to_markdown(floatfmt=".3f"), *pick_md,
          "\n\n## Per month: macro F1\n",
          res.pivot(index="month", columns="model", values="macro F1").to_markdown(floatfmt=".3f"),
          "\n\n## Logistic regression: features pushing toward up (+) or down (-), last fold\n",
          pd.concat([upcoef.head(8), upcoef.tail(8)]).to_frame("up minus down coef").to_markdown(floatfmt=".3f")]
    (OUT / f"{out}.md").write_text("\n".join(md), encoding="utf-8")
    print(summ.round(3).to_string())


if __name__ == "__main__":
    main()
