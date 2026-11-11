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
| Elvebredd value updates | `https://elvebredd.com/value-updates/<n>` (1–2387) | Probably a full changelog | Page data never loaded in testing. Unexplored. |

The old Google Sheet (`amvgg_trades_completed`, ~20k trades, May 20 to June 9, 2026) was only a format example and isn't used.

## Collection setup

- **`scraper.py`**: Python stdlib only.
  - `python scraper.py values` → `data/values/<elve|amvgg>/<YYYY-MM-DDTHHMMZ>.json.gz` (the full list for each snapshot)
  - `python scraper.py trades` → appends new trades to `data/trades/<YYYY-MM-DD>.jsonl`, deduped against today's and yesterday's files
  - `python scraper.py auto` → trades, plus values if the last snapshot is more than 4h45m old
  - `load_values(source)` / `load_trades()` → pandas DataFrames
  - Parsing: decodes the `self.__next_f.push` payload into `id:json` lines and walks the tree, following `$L<id>` references between lines.
- **GitHub Actions** (`.github/workflows/scrape.yml`) in private repo `Minuii/adoptme-ml`: cron at :07/:22/:37/:52, commits `data/` back to the repo. Manual run: Actions → scrape → Run workflow (`auto`/`values`/`trades`).
- **Minutes budget:** GitHub Pro = 3,000 min/month. Every run is billed as at least 1 min, so 4 runs/hour ≈ 2,980/month. If it runs out, the workflow pauses until the month resets. Fallback: 3 runs/hour.
- Storage is plain files rather than SQLite, because a database file rewritten every 15 min would bloat the git history.
- **Don't run the scraper locally and push.** It would conflict with the bot's commits. Run `git pull` to get the data.

## Open items

- [ ] AMVerse owner: ask for a full history export, and whether the public 31-day history may be pulled for every pet
- [ ] Look into Elvebredd `/value-updates` as a source of value history
- [ ] Watch the first days of scheduled runs: GitHub delays, minutes used, gaps in trades
- [ ] Map item names between Elve and AMVGG (and trade items) for joining

## Timeline

### 2026-11-11
- Reviewed the plan (blind second opinion from DeepSeek). Cut it to: AMVGG trades → Elve pet value changes, collect now, history is the hard go/no-go.
- Created `.env` (AMVerse key) and `.gitignore`. Key turned out invalid.
- Found the data sources above. AMVerse history is capped and bot-protected.
- Built `scraper.py`, first with SQLite, then switched to files for git. Fixed trade parsing (cards reference other payload lines via `$L<id>`; before the fix, 22 of 101 trades came out with one side missing).
- Measured trade churn: about 5 new per 90 s.
- Local Windows scheduled tasks were blocked by the permissions check, so collection moved to GitHub Actions. Created the private repo and verified both job types run on GitHub (3,527 Elve + 802 AMVGG items, trades committed).
