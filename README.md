# Adopt Me value tracker and forecast

**Live site: https://minuii.github.io/adoptme-ml/**

A value list for Adopt Me (Roblox) pets that puts the two big community value lists, [Elvebredd](https://elvebredd.com)
and [AMVGG](https://amvgg.com), side by side, with every logged value change, real trading activity, and a model that
forecasts which pets' Elvebredd values are likely to rise or drop over the next 7, 30 or 90 days. The forecasts are
checked against what actually happened, in public, on the site.

Not affiliated with Adopt Me, Uplift Games, Elvebredd or AMVGG.

## What the site shows

- **Values:** every item on both lists (about 3,500), filterable by variant (normal / neon / mega, fly / ride), rarity,
  category and AMVGG demand, with 30-day and 1-year changes. A side panel lists the 20 pets most likely to rise or drop.
- **Item pages:** current value on both lists, value history charts, the model's outlook, completed trades and trade
  offers from the last 7 days, and how the item actually trades against its listed value.
- **Value changes, Compare, Offers, Stats:** the change feed, a two-sided trade calculator, recent trade offers
  (no trader names), and data totals plus the forecast's live track record.

## How it works

```
scraper.py (every 15 min, GitHub Actions)  ->  data/          value lists, change logs, completed trades, offers, news
elve_model.py forecast (daily)             ->  results/       30 / 7 / 90-day calls, plus a saved copy of each day's calls
build_site.py (hourly)                     ->  site/*.json    -> GitHub Pages
track_record.py                            ->  scores each saved day's calls once its 7 / 30 / 90 days are over
```

1. **Collection.** A bot reads both value lists hourly, Elvebredd's and AMVGG's change logs, AMVGG's completed trades
   and both sites' trade offers every 15 minutes (trades every 5), and the official update posts from playadopt.me.
   Elvebredd's change log goes back to September 2023 (61,000+ changes), which is the model's training history.
2. **Model.** Gradient boosting (logistic regression at 90 days) on one row per pet variant per day. It predicts
   whether Elvebredd's value moves up, down or neither (by 2% / 5% / 10% at 7 / 30 / 90 days) from:
   the pet's own value history (recent changes, how often and how long ago it moved), what its other variants just did,
   the mood of the market and of its rarity, how often it is wanted versus offered in trade ads (counted once per
   poster per day, so spam doesn't count), and game news (new pets, pets leaving or returning).
   It predicts three variants per pet (normal no potion, neon fly ride, mega fly ride), the ones Elvebredd logs reliably.
3. **Testing.** Walk-forward by month: the model is trained only on data from before each test month (with a gap as
   long as the horizon), so it never sees the future. Features for a day use data up to the end of that day only.

## Results

Walk-forward tests, offers + news model, compared with "repeat the last change" and with the average pet.
"Up calls right" = share of "likely up" calls that rose by the threshold; "top 20" = mean change of the 20 strongest
up calls, with new picks every horizon so each bet counts once.

| Horizon | Threshold | Test months | Up calls right | Down calls right | Top 20 change | All pets | Repeat last change: up right, top 20 |
|---|---|---|---|---|---|---|---|
| 7 days | 2% | 19 | 51% | 58% | +6.1% | 0% | 18%, +1.4% |
| **30 days** | 5% | 17 | 44% | 53% | **+14.0%** | +0.1% | 29%, +4.0% |
| 90 days | 10% | 13 | 52% | 50% | +23% | +0.7% | 35%, +12% |

At 30 days the gain holds without penny pets and for each variant, and the top 20 beat the average pet in
17 of 17 months. Most values don't move in a given month (85% at 30 days), so the model calls few moves; when it does,
it is right about half the time, against 7–8% by chance.

**What didn't work** (kept here on purpose):

- *AMVGG moves first, Elvebredd follows* was the starting idea. As a plain rule it is worse than repeating the last
  change. As model features it helped at 7 days on the 3 months there is data for; not used until it holds longer.
- *Predicting how much* a value will move: the expected change and its 10–90% range barely beat "repeat the last
  change", and the range covered only 29% of real moves. The site shows chances, not amounts.
- *Gradient boosting at 90 days* lost to plain logistic regression, which the 90-day forecast now uses.

These are tests on past data. **The live track record** on the site's Stats tab scores the real daily calls, made
before the outcome, once their 7 / 30 / 90 days are over (first results 20 Nov 2026 for 7 days, 13 Dec for 30 days).

Full numbers: `results/*.md`. Every decision and finding, in order: `log.md`.

## Running it

```bash
python scraper.py auto            # one collection run (standard library only)
python build_site.py              # build site/*.json from data/
python -m http.server 8767 -d site
pip install -r requirements.txt   # for the model
H=30 python elve_model.py forecast   # today's 30-day calls (about 10 minutes, ~5 GB RAM)
H=30 python elve_model.py both       # walk-forward test; slow (1 h+), faster on a GPU with xgboost
python test_scraper.py && python test_track_record.py
```

`HANDOFF.md` describes every file, the rules (name matching, no leakage, git workflow with the bot) and the current state.

## Data and permissions

All data is in `data/` and public. Elvebredd's value change pages and AMVGG's pages are public; Elvebredd's trade
listings are used with the permission of its head value manager, and AMVGG's owner approved collecting from AMVGG.
The site shows items and aggregates only: no trader names or ids. Pictures come from the official Adopt Me wiki.
