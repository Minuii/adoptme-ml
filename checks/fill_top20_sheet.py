"""Fill in a top-20 check sheet (made by make_top20_sheet.py) once its check day is over.

    python checks/fill_top20_sheet.py checks/top20_rise_7d_2026-11-12.xlsx            # refuses before the check day ends (UTC)
    python checks/fill_top20_sheet.py <sheet> --force --out <copy.xlsx>               # test: use the newest values instead

Column G gets each pet's Elvebredd value for the predicted variant at the end of the check day (UTC): the newest value-list
snapshot taken up to then (snapshots are written whenever Elvebredd's list changes, so that is the value at that moment).
Formulas are kept and Excel recalculates them on opening; run `git pull --rebase origin main` first so data/ is current.
"""
import gzip
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Font

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scraper import DATA, elve_canonical, item_key, lines  # noqa: E402

COL = {"Normal No Potion": "rvalue - nopotion", "Neon Fly Ride": "nvalue - fly&ride", "Mega Fly Ride": "mvalue - fly&ride"}
SHEET, HEAD_ROW, FIRST, N = "Check in 7 days", 5, 7, 20


def main():
    args = sys.argv[1:]
    force = "--force" in args
    out = Path(args[args.index("--out") + 1]) if "--out" in args else None
    path = Path(next(a for a in args if a.endswith(".xlsx") and (out is None or Path(a) != out)))
    wb = load_workbook(path)
    ws = wb[SHEET]
    check_day = re.search(r"\d{4}-\d{2}-\d{2}", ws.cell(HEAD_ROW, 7).value)[0]
    cutoff = datetime.fromisoformat(check_day).replace(tzinfo=timezone.utc) + timedelta(days=1)  # end of the check day
    now = datetime.now(timezone.utc)
    if now < cutoff and not force:
        sys.exit(f"{check_day} isn't over yet in UTC (ends {cutoff:%Y-%m-%d %H:%M} UTC); nothing filled.")
    if force:
        cutoff = now

    snaps = [f for f in sorted((DATA / "values" / "elve").glob("*.json.gz"))
             if datetime.strptime(f.name[:16], "%Y-%m-%dT%H%MZ").replace(tzinfo=timezone.utc) <= cutoff]
    snap = snaps[-1]
    items = json.loads(gzip.decompress(snap.read_bytes()))
    canon = elve_canonical([i for i in items if i.get("type") == "pets"], [c for c in lines("elve_updates") if "newValue" in c])
    checked = (DATA / "values" / "checked.txt").read_text(encoding="utf-8").strip()
    if not force and checked < cutoff.strftime("%Y-%m-%dT%H%MZ"):
        sys.exit(f"the bot last checked the lists at {checked}, before the end of {check_day}: run `git pull` and try again.")

    filled = []
    for r in range(FIRST, FIRST + N):
        name, variant, before = ws.cell(r, 2).value, ws.cell(r, 3).value, ws.cell(r, 6).value
        it = canon.get(item_key(name))
        v = it.get(COL[variant]) if it else None
        if v in (None, ""):
            ws.cell(r, 11, "No Elvebredd value found automatically; fill in by hand.")
            continue
        ws.cell(r, 7, float(v))
        filled.append((name, variant, before, float(v)))
    stamp = f"{snap.name[:10]} {snap.name[11:13]}:{snap.name[13:15]} UTC"
    note = ws.cell(4, 1, f"Column G filled automatically on {now:%Y-%m-%d %H:%M} UTC from the site's Elvebredd snapshot of {stamp} "
                         f"(the newest one up to the end of {check_day}{'; TEST RUN with current values' if force else ''}).")
    note.font = Font(name="Arial", size=9, bold=True, color="C00000")
    ws.merge_cells(start_row=4, start_column=1, end_row=4, end_column=11)
    wb.calculation.fullCalcOnLoad = True  # Excel recalculates every formula when the file is opened
    wb.save(out or path)

    hits = sum(after / before - 1 >= 0.02 for _, _, before, after in filled)
    avg = sum(after / before - 1 for _, _, before, after in filled) / max(len(filled), 1)
    print(f"{out or path}: filled {len(filled)} of {N} from {snap.name}; rose 2%+: {hits} of {len(filled)} "
          f"({hits / max(len(filled), 1):.0%}); average change {avg:+.1%}")
    for name, variant, before, after in filled:
        print(f"  {name:24} {variant:17} {before:>10g} -> {after:<10g} {after / before - 1:+.1%}")


if __name__ == "__main__":
    main()
