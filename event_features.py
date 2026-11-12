"""Game-update features from playadopt.me/news (data/news.jsonl, one post per update, back to 2020).

    from event_features import event_features
    E = event_features(days, names)   # long table: day, name + feature columns, to merge into the model panel

A post goes live with the update (usually Friday 15:00-16:00 UTC) and Elvebredd reacts hours later, so a feature for
day t uses posts published up to the end of day t (UTC), the same cutoff as the values and the ad features.
Pets are found in a post's text by name, no LLM: a line that is exactly a pet's name (headings, egg tables, image alt
texts), or, for names long enough not to be ordinary words, the name inside a sentence.
"""
import re

import numpy as np
import pandas as pd

import scraper

LEAVING = re.compile(r"\b(?:leaving|last chance|retir\w*|no longer (?:be )?(?:available|obtainable)|final (?:week|weekend|days?)"
                     r"|going away|goes away|until it'?s gone|disappear\w*|ends? (?:soon|this|on|next))\b", re.I)
RETURNING = re.compile(r"\b(?:returns?|returning|is back|are back|back for|comeback)\b", re.I)


def post_pets(text, keys):
    """item_keys of the pets a post names. `keys`: item_key -> pet name."""
    found = set()
    for line in text.split("\n"):
        k = scraper.item_key(line)
        if k in keys:
            found.add(k)
        padded = f" {k} "
        for key in keys:
            # short one-word names ("Cat", "Bee", "Owl") only count on a line of their own
            if (len(key) >= 8 or " " in key) and f" {key} " in padded:
                found.add(key)
    return found


def tagged_posts(pet_names):
    keys = {scraper.item_key(n): n for n in pet_names}
    news = scraper.load_news()
    news["day"] = news.published.dt.tz_convert(None).dt.normalize()
    news["pets"] = [sorted(keys[k] for k in post_pets(t, keys)) for t in news.text]
    news["leaving"] = news.text.str.contains(LEAVING) | news.title.str.contains(LEAVING)
    news["returning"] = news.text.str.contains(RETURNING) | news.title.str.contains(RETURNING)
    return news


def event_features(days, pet_names):
    """Long table (day, name):

    market (same for every pet):
      ev_days_since_post   days since the last update post (capped at 14)
      ev_leaving_7         1 if an update post in the last 7 days talks about something leaving / ending
      ev_new_pets_7        log1p(pets named for the first time in a post in the last 7 days)
    per pet:
      ev_mention_7 / _30   1 if a post named the pet in the last 7 / 30 days
      ev_leaving_14        1 if the pet was named in a "leaving" post in the last 14 days
      ev_returning_14      1 if the pet was named in a "returns" post in the last 14 days (more supply)
      ev_age               log1p(days since the pet was first named in a post); empty for pets older than the news
    """
    news = tagged_posts(pet_names)
    days = pd.DatetimeIndex(days)
    names = pd.Index(sorted(pet_names), name="name")

    def daily(mask=None):  # day x pet: 1 if a post that day names the pet (optionally only posts matching mask)
        n = news if mask is None else news[mask]
        rows = [(d, p) for d, ps in zip(n.day, n.pets) for p in ps]
        m = pd.DataFrame(rows, columns=["day", "name"]).assign(v=1.0)
        return m.pivot_table(index="day", columns="name", values="v", aggfunc="max").reindex(index=days, columns=names).fillna(0)

    def within(M, n):
        return (M.rolling(n, min_periods=1).max() > 0).astype(float)

    mention = daily()
    feats = {"ev_mention_7": within(mention, 7), "ev_mention_30": within(mention, 30),
             "ev_leaving_14": within(daily(news.leaving), 14), "ev_returning_14": within(daily(news.returning), 14)}
    first = {}  # the day each pet was first named in a post (posts are sorted oldest first)
    for d, ps in zip(news.day, news.pets):
        for p in ps:
            first.setdefault(p, d)
    age = pd.DataFrame({p: (days - first[p]).days for p in names if p in first}, index=days).reindex(columns=names)
    feats["ev_age"] = np.log1p(age.where(age >= 0))

    post_days = pd.Series(1.0, index=news.day.unique()).reindex(days).fillna(0)
    last_post = pd.Series(np.where(post_days > 0, days, pd.NaT), index=days).ffill()
    market = pd.DataFrame({
        "ev_days_since_post": pd.Series((days - pd.DatetimeIndex(last_post)).days, index=days).clip(upper=14),
        "ev_leaving_7": news[news.leaving].groupby("day").size().reindex(days).fillna(0).rolling(7, min_periods=1).max().gt(0).astype(float),
        "ev_new_pets_7": np.log1p(pd.Series(list(first.values())).value_counts().reindex(days).fillna(0).rolling(7, min_periods=1).sum()),
    }, index=days)
    out = pd.concat({k: v.stack(future_stack=True) for k, v in feats.items()}, axis=1).rename_axis(["day", "name"]).reset_index()
    return out.merge(market.rename_axis("day").reset_index(), on="day", how="left")


if __name__ == "__main__":  # quick look: how many pets each post names, and the leaving / returning tags
    import elve_model
    log, _ = elve_model.contiguous_log()
    V, _, _ = elve_model.daily_values(log)
    names = sorted(set(V.columns.get_level_values("name")))
    news = tagged_posts(names)
    print(f"{len(news)} posts, {news.published.min().date()} -> {news.published.max().date()}; "
          f"{(news.pets.str.len() > 0).mean():.0%} name at least one pet; leaving {news.leaving.sum()}, returning {news.returning.sum()}")
    for _, r in news.tail(12).iterrows():
        print(f"{r.published:%Y-%m-%d %H:%M}  {'L' if r.leaving else ' '}{'R' if r.returning else ' '}  {r.title[:42]:42}  {', '.join(r.pets[:8])}")
    E = event_features(V.index, names)
    print(E.drop(columns=["name"]).groupby("day").mean().resample("QS").mean().round(3).tail(8).to_string())
