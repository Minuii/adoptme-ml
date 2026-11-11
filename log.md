# Project log

Running record of decisions, findings and setup. Newest entries at the bottom of each section; dated entries in the timeline.

## Goal

Predict Adopt Me pet value changes. Portfolio project first; if it works, use it for real trading (item-for-item only, no cross-trading). "Profit" = value gained/lost on a fresh account.

Core idea: Elvebredd's value team sets values partly from real trade proofs, and AMVGG completed trades are public and happen first. So **AMVGG trade prices should lead Elve value changes**. Elve value is the target, AMVGG data are inputs.

## Plan (agreed 2026-11-11)

| Phase | What | Status |
|---|---|---|
| 0 | Feasibility: find value history, start collecting | in progress |
| 1 | One table (item × day), target = up/flat/down over 3–7 days, pets only. Baselines: always-flat, repeat-last-change, AMVGG-gap rule | todo |
| 2 | Event features from a hand-made CSV of event dates (no LLM) | todo |
| 3 | Hype signals (YouTube/Reddit/TikTok, player counts) | deferred, optional |
| 4 | Logistic regression → gradient boosting, walk-forward time split, profit sim (only items with real trade volume) | todo |
| 5 | GitHub README, results chart, resume bullets from measured numbers only | todo |

Timeline: about 4 weeks of full-time work, mid-December to mid-January. Collection runs until then.
Kill rule: if the model can't beat the AMVGG-gap baseline on a time split, write up the negative result.

Changes from the original 10-week plan: dropped the separate Python refresher (learn by reading the code), the Roblox player count (same value for every item), LLM event tagging, "last year's change" (no year of history) and the 14-day horizon (pets move daily).

## Data sources

| Source | Where | What | Notes |
|---|---|---|---|
| Elvebredd values | `https://elvebredd.com/adopt-me-calculator` | 3,527 items: r/n/m values, no-potion, fly/ride variants, rarity, type | Embedded in the page as Next.js data (`initialPets`). Elve team edits values in a Google Sheet that feeds the site and a Discord bot. |
| AMVGG values | `https://amvgg.com/calculator` | 802 items: regular/neon/mega, fly/ride, no-potion, demand (Low/Medium/High) | Embedded as `pets`. Different scale from Elve, so compare within each list only. |
| AMVGG completed trades | `https://amvgg.com/trades/completed` | Latest ~100 completed trades: both users, items, N/M/F/R badges | Server-rendered, no JSON API (`/api/trades?status=completed` ignores the filter). No pagination. About 3.3 trades/min, so the page covers about 30 min. The owner (a friend) approved scraping. |
| AMVerse | `https://amverse.co` | Hourly snapshots of both lists, history charts | Public site only serves the last 750 hourly points (about 31 days) per pet, and returns 403 to non-browser clients. Not scraped (that would bypass their block). |
| AMVerse API v1 | `AMVerse-API/` Postman collection | Current values only, no history. 60 req/min, 36 ids per batch | Key in `.env` is rejected ("invalid or revoked"). Not needed anymore. |
| **Elvebredd value updates** | `https://elvebredd.com/value-updates/<n>` (1–2387+) | **Full change log since 2023-09-16.** Each change: item, variant label (e.g. "neon fly ride", "mega no potion"), previousValue, newValue, effectiveAt (to the second) | Embedded in each page (~2 MB). Batches range from 1 change (2024) to 238 (today). Latest batch number comes from links on the homepage. This is the main source of history. |
| **AMVGG value updates** | `https://amvgg.com/api/value-updates?limit=100&offset=N` | Change log since **2026-06-02** (~7,500 updates): item, previous/new Regular/Neon/Mega values, updatedAt | JSON API, max 100 per request. Returns **429 on fast bursts**, so wait ~6 s between pages. |

The old Google Sheet (`amvgg_trades_completed`, ~20k trades, May 20 to June 9, 2026) was only a format example and isn't used.

## Collection setup

- **`scraper.py`**: Python stdlib only.
  - `python scraper.py values` → `data/values/<elve|amvgg>/<YYYY-MM-DDTHHMMZ>.json.gz` (the full list for each snapshot)
  - `python scraper.py trades` → appends new trades to `data/trades/<YYYY-MM-DD>.jsonl`, deduped against today's and yesterday's files
  - `python scraper.py elve-updates` → new Elve update batches into `data/elve_updates/<YYYY-MM>.jsonl` (batches with no changes go to `empty.jsonl` so they aren't refetched)
  - `python scraper.py amvgg-updates` → new AMVGG changes into `data/amvgg_updates/<YYYY-MM>.jsonl` (deduped by id)
  - `python scraper.py auto` → trades. Every 4h45m it also does values, Elve updates (max 30 batches per run) and AMVGG updates. Then it rewrites `STATS.md`.
  - `python scraper.py stats` → rewrites `STATS.md`: snapshot counts, trades per day, latest trades, latest value changes from both sites
  - `fetch` retries 429/5xx/network errors with backoff (10 s → 80 s)
  - `load_values(source)` / `load_trades()` / `load_elve_updates()` / `load_amvgg_updates()` → pandas DataFrames (AMVGG changes in long format: one row per item × Regular/Neon/Mega)
  - Parsing: decodes the `self.__next_f.push` payload into `id:json` lines and walks the tree, following `$L<id>` references between lines.
- **GitHub Actions** (`.github/workflows/scrape.yml`) in private repo `Minuii/adoptme-ml`: cron at :07/:22/:37/:52, commits `data/` back to the repo. Manual run: Actions → scrape → Run workflow (`auto`/`values`/`trades`).
- **Minutes budget:** GitHub Pro = 3,000 min/month. Every run is billed as at least 1 min, so 4 runs/hour ≈ 2,980/month. If it runs out, the workflow pauses until the month resets. Fallback: 3 runs/hour.
- Storage is plain files rather than SQLite, because a database file rewritten every 15 min would bloat the git history.
- **Don't run the scraper locally and push.** It would conflict with the bot's commits. Run `git pull` to get the data.

## Open items

- [ ] AMVerse owner: ask for a full history export, and whether the public 31-day history may be pulled for every pet
- [x] Look into Elvebredd `/value-updates` as a source of value history (full log since 2023-09)
- [x] Check AMVGG for history (API back to 2026-06-02)
- [ ] Watch the first days of scheduled runs: GitHub delays, minutes used, gaps in trades
- [ ] Map item names between Elve and AMVGG (and trade items) for joining
- [ ] Rebuild daily Elve values per pet/variant by walking the change log back from today's snapshot
- [ ] Google Sheet that mirrors trades as they come in (needs a Google service account key as a repo secret)

## Timeline

### 2026-11-11
- Reviewed the plan (blind second opinion from DeepSeek). Cut it to: AMVGG trades → Elve pet value changes, collect now, history is the hard go/no-go.
- Created `.env` (AMVerse key) and `.gitignore`. Key turned out invalid.
- Found the data sources above. AMVerse history is capped and bot-protected.
- Built `scraper.py`, first with SQLite, then switched to files for git. Fixed trade parsing (cards reference other payload lines via `$L<id>`; before the fix, 22 of 101 trades came out with one side missing).
- Measured trade churn: about 5 new per 90 s.
- Local Windows scheduled tasks were blocked by the permissions check, so collection moved to GitHub Actions. Created the private repo and verified both job types run on GitHub (3,527 Elve + 802 AMVGG items, trades committed).
- **History found.** Elvebredd's `/value-updates/<n>` pages embed every change since 2023-09-16 (2,387 batches), so the Phase 0 history check passes. AMVGG's `/api/value-updates` goes back to 2026-06-02 (~7,500 updates). Backfilled both locally.
- First Elve backfill attempt died on a DNS blip, and probing AMVGG too fast got a 429. Added retry with backoff to `fetch` and a 6 s delay between AMVGG pages.
- Added `STATS.md`, rewritten every run, to watch data accumulate on GitHub. A Google Sheet mirror is planned next.
- AMVGG backfill done: 7,499 changes (2026-06-02 → 2026-11-10). About 1,170 of them are **demand changes** (e.g. Neon Medium → High) or single-value non-pet items, and `load_amvgg_updates()` keeps both. Demand shifts may lead value changes, so they're worth testing as a feature.
- The Elve backfill was too slow oldest-first (~14 s/batch, 1.9 MB pages; est. 4–9 h total). Switched to **newest first** so recent months land first, and restarted. 184 batches (Sep 2023 to Mar 2024) were already pushed.
- **Elve sync is commented out of `auto`** until the local backfill is pushed, so the bot and the local run don't both write `data/elve_updates/`. Re-enable it afterwards.
- No scheduled GitHub run has fired yet (only the two manual runs at 10:39/10:40 UTC). GitHub often delays a new repo's first cron runs. Check again later.
- **Dashboard:** https://claude.ai/artifact/7Hu3Cbe4ydRQtWqXKkmYjZ (private claude.ai artifact). It shows totals, value changes per month for both lists, trades per hour, most revalued items (90 days), most traded items, and the latest 60 changes. It runs on CSV snapshots made by `export_dashboard.py` (writes `dashboard_data/`, git-ignored) and uploaded to the artifact, so it doesn't update itself. To refresh: `git pull && python export_dashboard.py`, then ask Claude to re-upload. It can't read the private repo directly.
- **Pet explorer page** added to the dashboard (second tab): pick a pet, a variant (Normal/Neon/Mega) and potions (Fly Ride/No potion) to see its picture, current Elvebredd and AMVGG value, AMVGG demand, and step charts of both value histories. Neon/mega pictures are the base image with a CSS glow, because the official wiki has no separate variant images.
- **`fetch_images.py`**: downloads the official Adopt Me wiki catalog (`playadopt.me/discover/<category>`; robots.txt allows all) into `data/catalog.json` (3,238 items: 847 pets, 986 accessories, 728 toys, 275 transport, 158 gifts, 141 food, 103 strollers) and every thumbnail into `data/images/<category>/<kind>.png`. The catalog also has rarity, **origin event** (e.g. "Christmas Event (2019)"), egg flag and in-game cost, which could be useful event features.
- Dashboard images are base64 WebP (96px) in a data file, because the dashboard only shows `data:` images.
