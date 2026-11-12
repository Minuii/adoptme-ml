#!/usr/bin/env bash
# Commit data/ and STATS.md and push. Usage: bash .github/commit_data.sh <scraper job to rerun after a conflict>
# Two overlapping runs can both append to the same day's trades file, so a plain rebase can conflict.
# On conflict: drop our commit, take the newest data, scrape again on top of it (dedupes), retry.
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
for attempt in 1 2 3; do
  git add data STATS.md
  git diff --cached --quiet && exit 0
  git commit -q -m "data: $(date -u +%Y-%m-%dT%H:%MZ)"
  git pull -q --rebase && git push -q && exit 0
  git rebase --abort 2>/dev/null || true
  git fetch -q && git reset -q --hard origin/main
  python3 scraper.py "$1"
done
exit 1
