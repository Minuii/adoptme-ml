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
- **Elve backfill complete:** all 2,387 batches, **61,403 value changes** from 2023-09-16 to 2026-11-11, with no missing batches, duplicates or broken lines. Pushed, and `sync_elve_updates(limit=30)` is back on in `auto`.
- GitHub's cron never fired: 0 scheduled runs in ~4 h, even after disabling and re-enabling the workflow. Moving to an **external trigger**: cron-job.org POSTs to `/repos/Minuii/adoptme-ml/actions/workflows/scrape.yml/dispatches` every 15 min with a fine-grained token (this repo only, Actions read/write). The user is setting it up. Once runs appear, remove the `schedule:` block from `scrape.yml` and log the token's expiry date.
- **cron-job.org working:** first confirmed run 15:45 UTC (204 → GitHub run succeeded), next every :00/:15/:30/:45. Removed the dead `schedule:` block. The GitHub token is set to **never expire** (scoped to this repo, Actions read/write only). If runs stop, check cron-job.org's history for 401s, and revoke the token on GitHub if it ever leaks.
- Dashboard refreshed with the full history (61,403 Elve changes, 39 months of monthly data, 73,762 pet history points).
- The workflow's commit step now **retries on conflict**: two overlapping runs at 15:04 both appended to the same trades file and the second failed. It now drops its commit, resets to the newest `main`, scrapes again (dedupes) and retries up to 3 times.
- No scheduled GitHub run has fired yet (only the two manual runs at 10:39/10:40 UTC). GitHub often delays a new repo's first cron runs. Check again later.
- **Dashboard:** https://claude.ai/artifact/7Hu3Cbe4ydRQtWqXKkmYjZ (private claude.ai artifact). It shows totals, value changes per month for both lists, trades per hour, most revalued items (90 days), most traded items, and the latest 60 changes. It runs on CSV snapshots made by `export_dashboard.py` (writes `dashboard_data/`, git-ignored) and uploaded to the artifact, so it doesn't update itself. To refresh: `git pull && python export_dashboard.py`, then ask Claude to re-upload. It can't read the private repo directly.
- **Pet explorer page** added to the dashboard (second tab): pick a pet, a variant (Normal/Neon/Mega) and potions (Fly Ride/No potion) to see its picture, current Elvebredd and AMVGG value, AMVGG demand, and step charts of both value histories. Neon/mega pictures are the base image with a CSS glow, because the official wiki has no separate variant images.
- **`fetch_images.py`**: downloads the official Adopt Me wiki catalog (`playadopt.me/discover/<category>`; robots.txt allows all) into `data/catalog.json` (3,238 items: 847 pets, 986 accessories, 728 toys, 275 transport, 158 gifts, 141 food, 103 strollers) and every thumbnail into `data/images/<category>/<kind>.png`. The catalog also has rarity, **origin event** (e.g. "Christmas Event (2019)"), egg flag and in-game cost, which could be useful event features.
- Dashboard images are base64 WebP (96px) in a data file, because the dashboard only shows `data:` images.
- Explorer controls changed to Elvebredd-style **F / R / N / M** toggles (fly and ride combine freely; N and M exclude each other; click again for normal), using Elvebredd's own colors (`--fly` #2f98cc, `--ride` #ed2c79, `--neon` #8cc63f, `--mega` #822ce2 gradients). The glow on pictures was removed. Matching letter badges sit next to the pet name. `pets.csv` now has values and AMVGG demand for all 12 variants (r/n/m × np/f/r/fr). Value-change history only exists for **fly ride and no potion** on both sites, so fly-only and ride-only show current values only.
- **GitHub Pages value list** (`site/index.html` + `build_site.py` + `.github/workflows/pages.yml`). Replaces the manual-refresh claude.ai dashboard as the main view: the workflow rebuilds `site/data.json` from `data/` hourly and deploys it, so it stays current on its own. It shows every item on either list (3,473; 802 on AMVGG), joined by name. Filters: source (Both/AMVGG/Elvebredd), variant (Normal/Neon/Mega), potion (Fly Ride/Fly/Ride/No Potion), category, rarity, AMVGG demand, search. Sorts: value, 30-day rise/drop, and "AMVGG vs Elve gap" (difference of an item's percentile rank on each list, since the two use different scales). A second tab lists every logged value change. Clicking an item shows both value histories and the full variant × potion table. Filters live in the URL hash, so views can be shared. Style mixes AMVGG (charcoal, cyan, Baloo 2 + Montserrat) and playadopt.me (pink, rarity colours). Images hotlink the official wiki CDN from `catalog.json`.
  - Elve's change log has gaps: e.g. "default fly ride" is barely logged after 2023, and values were rescaled since. A variant's history only counts (chart, % change) when its last logged value matches today's snapshot. % changes are blank when the window reaches back before a source's log starts (AMVGG 2026-06-02).
  - Needs: `data/catalog.json` committed (for images and origins), and Pages enabled with Source = GitHub Actions. The repo is private, so Pages needs a paid plan or a public repo.
- **Plan change: Elve-only model first.** Train on Elvebredd's change log alone for now. AMVGG value history and the trade log keep collecting on GitHub and get added as features once they have enough history (AMVGG log starts 2026-06, trades started today).
- **`elve_model.py`** (scikit-learn, no PyTorch: tabular data suits boosted trees). Rebuilds daily values per pet variant from the change log (newest unbroken run of batches only, so it grows as the backfill fills in). Target: 7-day move up / flat / down, with flat meaning under 2%. Features: own momentum (1/7/30/90 d, up/down counts, days since change, last change), what the pet's other variants just did, up/down share within the pet's rarity and across the market, value level, rarity, variant. Walk-forward by month with a 7-day gap. Writes `results/elve_model.md` and `results/elve_model_folds.csv`.
- **Only 3 variants are predicted: default no potion, neon fly ride, mega fly ride.** Rebuilt values match today's snapshot for about 90% of these, versus about 76% for default fly ride, neon no potion and mega no potion, which Elve often changes without logging. Those three only feed the pet-level features.
- **First results** (window 2025-07-14 → 2026-11-10, 13 test months; class shares down 6.0%, flat 89.1%, up 4.9%):

  | Model | Up precision | Down precision | Log loss | Top-20 picks, mean 7d change |
  |---|---|---|---|---|
  | Always flat | 0 | 0 | 0.81 | -0.1% |
  | Repeat last change | 18% | 21% | 2.17 | +1.7% |
  | Logistic regression | 44% | 49% | 0.41 | +3.8% |
  | Gradient boosting | 48% | 50% | 0.39 | **+5.1%** |

  The average across all variants is -0.2%. Gradient boosting's top 20 beat that average in 12 of 13 months; the miss is November 2026, which has only 3 days of targets so far. The strongest signals are momentum (last change, recent up count), what other variants of the same pet just did, and value level (pricier pets drift up). Caveats: picks overlap from day to day, so there are far fewer independent bets than rows; the score is Elve value gained, not tested against real trade prices or liquidity yet; about 10% of predicted variants still have unlogged changes.
- **AMVGG trade history check.** Completed trades have no archive anywhere public. The completed page shows only the latest ~100 and has no pagination. `/api/trades` turned out to be **trade ads**, not completed trades: author, `offering` and `lookingFor` items with type (e.g. `mfr`, `nfr`), and `publishedAt`. It ignores `status` but pages backwards with `?limit=100&cursor=<ISO time>` (response has `pagination.nextCursor`). Ads go back to about late August 2026 (a cursor at 2026-09-01 returns ads from Aug 25–31, one at 2026-07-01 returns nothing). Recent volume is about 100 ads per 10 minutes, so a full backfill would take ~140 requests per day of history, roughly 18 h for Sep–Nov at 6 s per request. Ads could serve as a demand signal ("looking for" vs "offering" counts per pet). AMVGG's own database must hold every completed trade, so the realistic way to get trade history is to ask the owner for an export.
- **Elvebredd trade ads check.** The trade center (`/trade-center`) loads listings client-side from `/api/recent-listings?limit=<≤50>&offset=N&game=Adopt+Me`. Each listing has the owner, `ownerGive` / `ownerGet` items with fly/ride/neon/mega flags, `timeCreated`, and `difference` (value gap by Elve's own values). Offset 0 returns active listings; deep offsets return an archive in id order, from about Feb 2025 (offset ~62M is 2026-10-02), which works out to roughly 100k listings a day. "Completed" fields exist but have no counterparty (e.g. a Feb 2025 listing marked completed in Jan 2026), so they look like closures, not real trades. Placeholder items such as "Add" and "Add Big" would need filtering.
  - **robots.txt disallows `/api`** (also `/adopt-me-calculator/` and `/profile`). I made about 15 probe requests before seeing this. No Elve listings collector should be built without permission from the Elve team. Ask them for access or an export. `/value-updates/<n>` pages are allowed.
- **Elve listings approved.** David (head value manager, under Elve) said using the trade listings is fine. They have no export, so history comes only from sampling the archive.
- **Trade-ad collection added** (`scraper.py`):
  - `amvgg-ads`: AMVGG ads since the newest stored, **max 4 pages (400 ads) per run**. Real rate is about 100 ads/min at peak (the earlier "100 per 10 min" estimate came from a quiet late-night page), roughly 50–150k/day. Collecting everything would mean ~20 MB/day in git and runs over a minute, so busy hours are sampled and quiet hours are complete.
  - `elve-ads`: Elve's page 0 (newest 50 posted/renewed listings) fetched 3 times, 10 s apart, Adopt Me only. Stored per (id, update time), since renewals show the listing is still active.
  - Both run in `auto` after trades, inside try/except so ad failures never block trades or values. A catch-up run takes ~40 s.
  - Storage: `data/ads/<source>/<day>/<run time>.jsonl.gz`, one small gzip per run (4–13 KB), so git stores each ad once, compressed. Items are `"Name|BADGES"` strings (e.g. `Bat Dragon|MFR`). AMVGG "signs" with no item become `#Add|`, `#Upgrade|`. Elve rows also carry `diff` (Elve-value difference of the offer) and `created`.
  - `load_ads(source)` reads bot files and backfill together.
- **`ads_backfill.py`** (local, resumable, writes `data/ads/<source>/backfill/<month>.jsonl.gz` + `progress.txt`): AMVGG = 1 page of 100 per hour of history from 2026-08-20 (~2k requests at 6 s ≈ 3.5 h). Elve = 10,000 pages of 50 spread evenly over the archive (≈ 500k listings, ~1.5 s each ≈ 4–5 h). The two are different sample rates, so features must use **shares** (pet's share of ads that day), not raw counts.
- **GitHub scheduled runs had not fired** as of 14:51 UTC (only the 10:39/10:40 manual runs), so no trades were collected after 10:40.
- First GitHub run with ads (manual, 15:04 UTC): 102 trades, 100 AMVGG ads, 60 Elve ads collected. It failed at push because I had also started a trades-only run at the same moment: both appended to `data/trades/2026-11-11.jsonl` and the rebase conflicted. Added `.gitattributes` with `data/**/*.jsonl merge=union` so concurrent appends (bot runs or a local push) merge instead of failing. Duplicate lines are possible after a union merge, so loaders should dedupe on id.
- **Elve listings API gotcha:** past the end of the archive (around offset 70M today) it doesn't return an empty page. It falls back to the newest listings. The archive order is also only roughly by update time (68M → Nov 8, 70M → Nov 6). The backfill's end search now treats "page updated within the last hour" as past the end.
- **Moved everything to the live site** (https://minuii.github.io/adoptme-ml/, public) and stopped updating the claude.ai artifact; `export_dashboard.py` was removed. The site now has:
  - a **Stats** tab: totals, value changes per month (both lists), trades collected per hour (last 3 days), most traded (7 days) and most revalued (90 days) items. Built into `site/stats.json` by `build_site.py`, aggregates only, so no trader names are published.
  - Elvebredd-style **F / R / N / M toggles** in the filter bar and the item popup (fly and ride combine; N and M exclude each other; click again for normal), in Elvebredd's own colors. The neon/mega glow is gone; pictures carry small N/M/F/R badges instead.
- **Site rebuilds:** `pages.yml`'s hourly cron never fired (same GitHub problem as scrape). The scrape workflow now dispatches `pages.yml` on its :00 run every 3 hours (dispatches from the workflow token do start other workflows; plain pushes don't). Site edits still deploy on push.
- **Actions minutes are tight.** Scrape runs take 45–60 s, billed as 1 min each (2 min once over 60 s). 96 runs/day ≈ 2,900 min/month plus ~240 for site builds, against Pro's 3,000. Dropped `setup-python` (stdlib only, runner's python3) to keep runs under a minute. If GitHub's usage page shows it running over, set cron-job.org to every 20 minutes (the trade page holds ~30 min).
- **Trade collection fixes (16:05 UTC):** AMVGG's completed page is a Next.js cached page, up to 5 min stale (`s-maxage=300`). The 16:00 run got a stale copy (0 new) and 16:03 got 101/101 new, so trades in between were missed. Now fetched with a throwaway `?t=<time>` query, which returns a fresh render. Measured fresh turnover at evening peak: **~6 trades/min, so the page spans ~17 min**. 15-minute polling is just enough; a run reporting "N of N new" means a likely gap. Also, item tiles with all-digit keys were parsed as empty "trades" (1 stored on 2026-11-11, `sides: []`): those are now skipped, and loaders should drop trades without 2 sides.
- **Decision:** keep polling every 15 minutes, and keep the repo private (no unlimited minutes, raw data stays private). Accepts small trade gaps at peak hours (~6/min, page spans ~17 min); daily trade features tolerate that.
- **AMVGG full item list.** AMVGG's calculator only carries the 802 pets, and only their fly ride values. Its `/values/<kind>` pages have everything: `/values/pets` has the same 802 pets with all 12 variants (no potion, fly, ride), plus `origin` and `lastUpdatedAt`. Nine more pages (eggs, food, gifts, houses, petwear, stickers, strollers, toys, vehicles) add **953 non-pet items**, each with one `value` and `demand`, listed under `items`. No pets were missing. `snapshot_values` now saves all 10 pages (1,755 items, ~57 KB gz) with a `kind` field per item. Snapshots before this one are pets only, with no `kind`. The site goes from 802 to 1,755 AMVGG items, and AMVGG no-potion/fly/ride pet values now show up. Houses have no Elvebredd match (Elve has no house category).
- Site name joins now ignore accents ("Tió De Nadal" vs "Tio De Nadal").
- **Site restyled after the old claude.ai dashboard** (user preferred it): plain light/dark theme, serif title, underlined tabs (Values / Value changes / Stats), the value list as a simple table, and an item page (replacing the popup) with the picture, both current values, F/R/N/M toggles, and two large d3 history charts with axes and hover tooltips, plus the variant × potion table. Stats tab ported from the old Overview (KPI cards, monthly line chart, hourly bars, tables with inline bars). d3 7.9.0 from cdnjs.
