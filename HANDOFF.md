# HANDOFF — read this first

For any AI (or person) picking this project up. It tells you what exists, what state it is in, and what to do next.
The full history of every decision and finding is in `log.md` (newest at the bottom). **Add to `log.md` whenever you decide
or find something**, and update the "Current state" and "Next steps" sections here when they change.

_Last updated: 2026-11-12._

## What this project is

Adopt Me (Roblox) pet-value tracking and prediction.
1. **Collects** value lists, value-change logs, completed trades, trade offers and game-update news from Elvebredd,
   AMVGG and playadopt.me, into `data/`. A GitHub Actions bot runs every 15 minutes.
2. **Publishes** a value-list website: https://minuii.github.io/adoptme-ml/ (repo `Minuii/adoptme-ml`, public).
3. **Predicts** Elvebredd value moves per pet variant, 7 / 30 / 90 days ahead (`elve_model.py`). Heavy runs happen on Kaggle (GPU).

## Files

| File | What it does |
|---|---|
| `scraper.py` | All collectors. `python scraper.py auto` is what the bot runs; `health` exits 1 if any collector has gone quiet. The docstring at the top lists every subcommand. Also has the shared helpers `item_key()` (name matching across sites), `elve_canonical()` (Elve's duplicate entries), `load_*()` loaders. |
| `ads_backfill.py` | One-off, resumable offer-history backfill (AMVGG + Elve). **Done**; don't rerun. |
| `ad_features.py` | Per-pet daily offer features (wanted vs offered shares). |
| `event_features.py` | Per-pet and market features from playadopt.me news posts (new pets, leaving, returning). |
| `amvgg_features.py` | Per-pet daily features from AMVGG's own change log (has AMVGG already moved?). Only from 2026-07 on. |
| `elve_model.py` | Builds the daily value panel and features, and runs walk-forward tests. Modes are listed in its docstring: (none), `ads`, `events`, `both`, `amvgg`, `size`. Env vars: `H` = horizon in days (default 7), `FLAT` = flat band, `VALUE_FLOOR` = smallest value counted in the "no penny pets" picks (default 0.25). |
| `test_scraper.py` | Checks for name matching and the page parser, no network: `python test_scraper.py`. Run it after touching `scraper.py`. |
| `requirements.txt` | What the model needs (the collectors and the site use the standard library only). |
| `build_site.py` | Builds `site/data.json`, `site/stats.json`, `site/ads.json` from `data/`. |
| `site/index.html` | The website (single page, d3). Run locally: `python -m http.server 8767 -d site`. |
| `fetch_images.py` | Official wiki catalog → `data/catalog.json` (rarity, origin event, images). |
| `results/` | Model results (`*_model*.md` summaries, `*_folds.csv` per month, `forecast*.csv`). |
| `STATS.md` | Auto-written data summary (bot). |
| `.github/workflows/scrape.yml` | Bot. Triggered by workflow_dispatch from an external cron (GitHub's own cron barely fires). Its :00 run also checks values hourly, collects news, and dispatches `pages.yml`. Each run then polls trades twice more, 5 minutes apart, and ends with `scraper.py health`. Commits go through `.github/commit_data.sh`. |
| `.github/workflows/forecast.yml` | Daily (dispatched by the scrape workflow's 01:00 UTC run): `H=30 python elve_model.py forecast` → commits `results/direction_30d.csv`, then rebuilds the site. ~10 min on GitHub. |
| `.github/workflows/pages.yml` | Builds and deploys the site. |
| `AMVerse-API/` | A Postman collection, unrelated to the pipeline. |

## Data (`data/`)

- `values/<source>/*.json.gz`: full value lists (snapshot written only when the list changed; `checked.txt` = last check).
- `elve_updates/`: Elvebredd's change log since 2023-09 (old → new value per variant). **This is the model's training data.**
- `amvgg_updates/`: AMVGG's change log (only since 2026-06-02, fly ride only).
- `trades/<day>.jsonl`: AMVGG completed trades (since 2026-11-11; only ~100 visible at a time, so polling must keep up).
- `ads/<source>/...`: trade offers (bot files + `backfill/`). Elve back to 2025-02, AMVGG back to 2026-08-20.
- `news.jsonl`: playadopt.me/news posts since 2020.
- `catalog.json`, `images/`, `amvgg_coefficients.json` (AMVGG's per-category potion multipliers).

## Rules and gotchas (important)

- **Git:** the bot commits `data:` every 15 minutes. Always `git pull --rebase origin main` before you push (plain `git pull --rebase` fails here: "Cannot rebase onto multiple branches"). Other AI sessions may be working in the repo at the same time, so check `git log origin/main` before adding a log entry. `data/**/*.jsonl` uses `merge=union`, so dedupe on id when loading.
- **Commit identity:** the repo uses the GitHub no-reply email. Don't commit with a personal email.
- **Permissions:** Elvebredd's robots.txt disallows `/api`. Its head value manager approved using the trade listings. Don't add new Elve `/api` collectors without asking. AMVGG and playadopt.me are fine.
- **Site privacy:** the site shows aggregates and items only. No trader names or ids on the site (raw data in the repo is public, which the user accepted).
- **Name matching:** always go through `scraper.item_key()` and `elve_canonical()`. Sites differ in case, accents, "The", and typos (`NAME_ALIASES`).
- **Model universe:** only the 802 pets AMVGG also lists. Only 3 variants are predicted (default no potion, neon fly ride, mega fly ride), because Elve logs the other three unreliably.
- **No leakage:** features for day t use data up to the end of day t only. Training stops H days before each test month.
- **Offer features are shares, not counts** (the sampling rates differ by source and period).
- **A failed scrape run usually means `health` found a stale collector** (GitHub emails the owner). Open the run's last step: it lists each collector with the age of its newest data. Data is committed before that step, so nothing is lost by the failure itself.
- **Reading the results tables:** the headline "top-20 mean" counts overlapping daily picks. Trust the *new picks every H days* column and the month-resampled range more; *value >= 0.25* shows whether penny pets carry the result. Results made before 2026-11-12's scoring change (`elve_model.md`, `events_model*.md`, `ads_model.md`) don't have these columns, and they used the old uncapped `age_days`, so new runs won't match them exactly.
- **scikit-learn quirk:** histogram boosting crashes on columns that are constant in training. `varying()` drops them per fold.
- **Kaggle:** notebook `minii23/notebook6bbaa04ff7` (GPU T4). It clones the repo (`--depth 1`), so **push before running**. Easiest from this PC with the Kaggle CLI: `kaggle kernels pull minii23/notebook6bbaa04ff7 -p <dir> -m`, edit the cells in the `.ipynb`, `kaggle kernels push -p <dir>` (starts a full background run, like *Save & Run All*), `kaggle kernels status ...`, then `kaggle kernels output minii23/notebook6bbaa04ff7 -p <dir>`. The notebook copies `results/` to its output and deletes the clone, so the download is small. The CLI sometimes times out; the browser works too (drafts die when the tab sleeps, so use *Save Version*). On a GPU the boosting model is XGBoost, locally it's scikit-learn, so numbers differ slightly. The last full run (4 jobs: 30-day both / size / news, 7-day size) took ~1.5 h.
- A full local model run takes ~1 h+ and ~4 GB RAM. Use `python elve_model.py <mode> 1` (last month only) for smoke tests, and don't commit the results files those produce.

## Model results so far (gradient boosting, Kaggle, full history)

**Current numbers, stricter scoring (2026-11-12, 30 days):** gradient boosting's top-20, new picks every 30 days, gains
**+13.9% a month** (90% range over months +11.2 to +17.0%), against +0.5% for all pets and +5.5% for repeat-last-change;
it beats the average pet in 31 of 33 months, and the gain holds without penny pets and for each kind (default / neon /
mega +13.9 / +11.1 / +10.1%). News adds nothing to the picks at 30 days (it helps down calls only). On the offer months
(2025-06 on) offers lift the overlapping picks from +11.0% to +13.2%, but non-overlapping both are ~+14%: a small gain.
Details in `log.md` and `results/events_model_30d.md`, `both_model_30d.md`, `size_model_30d.md`. The older table below
used the looser scoring:

| Horizon | Up precision | Down precision | Top-20 picks' mean change | All pets | Notes |
|---|---|---|---|---|---|
| 7 days, base | 38% | 42–43% | +4.4% / week | ~0% | ~11x chance on up calls |
| 7 days, + news | 35% | 50% | +4.3% | | news helps drops only |
| 7 days, + offers (2025-05 on) | 46 → 48% | 54 → 55% | +4.5 → +5.5% | | small, consistent gain |
| **30 days, + news** | 40% | 52% | **+12.9% / month** | +0.5% | best so far; better in 25 of 34 months |
| 90 days, + news | 44% | 46% | +22.5% / 90 d | +2.8% | not better than "repeat last change" (macro F1 0.48 vs 0.43): not worth it |

Recall is low everywhere (the model calls few moves, but is right about half the time). **30 days is the chosen horizon.**

## Current state (2026-11-12)

- Bot, site, all backfills: done and running. The bot now polls completed trades every 5 minutes (3 polls per run) and checks its own collectors at the end of each run.
- **Site (2026-11-12):** item pages show trading activity for the last 7 days (completed AMVGG trades in total and for the chosen variant, wanted vs offered on each site, the 5 latest trades as item chips, no trader names) from `site/activity.json`, which `build_site.py` writes. Every value also shows "≈ X Frost Dragons (FR)": Frost Dragon fly ride is the yardstick that makes the two lists' scales comparable, also used for the Compare totals. AMVGG values it only calculates from fly ride (773 pets, the `Ad` list in `data.json`) are dotted with a tooltip. Blank 30-day changes show "–" with the reason, offer cards say why they can't be valued, and the Stats tab shows offers collected in the last 24 h. History charts have a soft gradient fill under the step line.
- **Scoring was tightened (2026-11-12, see log.md):** per-kind and no-penny-pet picks, non-overlapping picks, a month-resampled range, average precision and precision at 30% recall; `age_days` is capped. All earlier Kaggle numbers in the table above predate this.
- **AMVGG test (local, `results/amvgg_model*.md`):** the plain rule "AMVGG moved, so Elve will follow" is worse than repeat-last-change. As model features AMVGG's moves helped a lot at 7 days, but on 3 test months only, and gave no clear answer at 30 days (1 test month). Promising, not proven.
- **Site forecast (2026-11-13):** `elve_model.py forecast` trains the offers + news classifier on all rows with a known 30-day outcome and calls the newest day; `build_site.py` turns `results/direction_30d.csv` into `site/forecast.json`; item pages show it. Runs daily on GitHub (scikit-learn); the calls agree with Kaggle's XGBoost (correlation 0.95 on P(up) and P(down)). Most calls are "no clear move" (2,245 of 2,406), ~130 down, ~30 up.
- **Full-history Kaggle results with the stricter scoring are in (2026-11-12, see the summary above and log.md).** The 30-day classifier's gain survives every check. The **size model does not** clear the bar for showing amounts: its rank IC (0.35 for the median, 0.33 for the two-part) is barely above repeat-last-change (0.33), and its 10–90% range covers 82% of all outcomes but only 29% of real moves (it is a narrow band around "no change"). At 7 days half its ranges have zero width. Today's forecast is in `results/forecast_30d.csv`.

## Next steps

1. **Forecast on the site: done (2026-11-13).** Item pages show "Next 30 days: model outlook" for the 3 predicted variants (likely up / likely down / no clear move, with P(rise of 5%+) and P(drop of 5%+)) and the backtest from `results/both_model_30d_folds.csv`. Check after a few days that `forecast.yml` runs daily, and every month or two compare old calls with what happened (the backtest is the promise the page makes).
2. Size model, if it's worth another try: train the range on movers separately (the range is now dominated by the ~85% flat rows), or show only P(up/down) and the typical size of a past rise / drop per pet.
3. Use the 30-day offers + news model (`both`) as the forecast model: same picks as base, better down calls (down average precision 0.35 → 0.39).
4. Rerun `python elve_model.py amvgg` (7 and 30 days) every month or so; it runs locally in ~10 minutes. Add AMVGG features to the main model once they have helped over 6+ test months.
5. Later: trade-volume features once trades have a few months of history (started 2026-11-11; complete only since the 5-minute polling of 2026-11-12).
6. After a week, check the trades for full-page runs again (a poll that finds 90+ new trades): if any are left, poll more often.
