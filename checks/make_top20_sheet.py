"""Top 20 most likely to rise in 7 days -> an Excel sheet to check by hand a week later."""
import csv, json, sys
from datetime import date, timedelta
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(sys.argv[1])
OUT = ROOT / "checks"
sys.path.insert(0, str(ROOT))
from scraper import item_key  # noqa: E402

head, *rows = (ROOT / "results" / "direction_7d.csv").read_text(encoding="utf-8").splitlines()
asof = head.split()[3]
check_day = (date.fromisoformat(asof) + timedelta(days=7)).isoformat()
fc = list(csv.DictReader(rows))
site = {item_key(i["name"]): i for i in json.loads((ROOT / "site" / "data.json").read_text(encoding="utf-8"))["items"]}

KEY = {"default no potion": "r-np", "neon fly ride": "n-fr", "mega fly ride": "m-fr"}
VAR = {"r": "Normal", "n": "Neon", "m": "Mega"}
POT = {"fr": "Fly Ride", "f": "Fly", "r": "Ride", "np": "No Potion"}
FORMS = [f"{v}-{p}" for v in VAR for p in POT]
form_name = lambda k: f"{VAR[k[0]]} {POT[k[2:]]}"

best = {}  # one row per pet: its likeliest variant, like the site's panel
for r in fc:
    p = float(r["p_up"])
    if r["name"] not in best or p > float(best[r["name"]]["p_up"]):
        best[r["name"]] = r
top = sorted(best.values(), key=lambda r: -float(r["p_up"]))[:20]

ARIAL = "Arial"
f_body, f_bold = Font(name=ARIAL, size=10), Font(name=ARIAL, size=10, bold=True)
f_title, f_note = Font(name=ARIAL, size=14, bold=True), Font(name=ARIAL, size=9, italic=True, color="595959")
f_input = Font(name=ARIAL, size=10, color="0000FF")
f_head = Font(name=ARIAL, size=10, bold=True, color="FFFFFF")
fill_head, fill_input = PatternFill("solid", fgColor="2F4F4F"), PatternFill("solid", fgColor="FFFF00")
fill_example = PatternFill("solid", fgColor="F2F2F2")
thin = Side(style="thin", color="BFBFBF")
box = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap = Alignment(wrap_text=True, vertical="center")

wb = Workbook()
ws = wb.active
ws.title = "Check in 7 days"

ws["A1"] = "Adopt Me: 20 pets most likely to rise on Elvebredd in the next 7 days"
ws["A1"].font = f_title
info = [f"Forecast as of {asof} (end of day UTC). Check on {check_day} or later: look up each pet's Elvebredd value for the variant in column C "
        "(elvebredd.com, or the item page on minuii.github.io/adoptme-ml) and type it into column G.",
        "A rise counts when the value is up 2% or more (the 7-day model's threshold). One row per pet: the variant it is likeliest to rise in "
        "(the model only predicts Normal No Potion, Neon Fly Ride and Mega Fly Ride).",
        "Legend: yellow cells with blue text = fill these in. Everything else is the forecast or a formula. Row 6 is a made-up example; "
        "leave it out of the totals (it is not counted)."]
for i, t in enumerate(info, start=2):
    ws.cell(i, 1, t).font = f_note
    ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=11)
    ws.cell(i, 1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[i].height = 26

H = ["Rank", "Pet", "Variant predicted", "Chance of a 2%+ rise in 7 days", "Chance of a 2%+ drop in 7 days",
     f"Elvebredd value on {asof}", f"Elvebredd value on {check_day} (fill in)", "Change", "Rose 2%+?", "AMVGG value now (same variant)", "Notes (optional)"]
HR = 5
for c, t in enumerate(H, 1):
    cell = ws.cell(HR, c, t)
    cell.font, cell.fill, cell.alignment, cell.border = f_head, fill_head, Alignment(wrap_text=True, vertical="center", horizontal="center"), box
ws.row_dimensions[HR].height = 44

# example row: realistic values showing the expected format; excluded from the summary
ex = HR + 1
for c, v in enumerate(["e.g.", "Example Dog", "Neon Fly Ride", 0.62, 0.02, 10, 10.5], 1):
    ws.cell(ex, c, v)
ws.cell(ex, 8, f"=IF(G{ex}=\"\",\"\",G{ex}/F{ex}-1)")
ws.cell(ex, 9, f"=IF(G{ex}=\"\",\"\",IF(H{ex}>=0.02,\"Yes\",\"No\"))")
ws.cell(ex, 11, "Example only: 10 -> 10.5 is +5%, so Yes")
for c in range(1, 12):
    ws.cell(ex, c).font, ws.cell(ex, c).fill, ws.cell(ex, c).border = Font(name=ARIAL, size=10, italic=True, color="7F7F7F"), fill_example, box

first = ex + 1
for i, r in enumerate(top):
    row = first + i
    it = site.get(item_key(r["name"]), {})
    k = KEY[r["label"]]
    a_now = (it.get("A") or {}).get(k)
    vals = [i + 1, r["name"], form_name(k), float(r["p_up"]), float(r["p_down"]), float(r["value"]), None,
            f"=IF(G{row}=\"\",\"\",G{row}/F{row}-1)", f"=IF(G{row}=\"\",\"\",IF(H{row}>=0.02,\"Yes\",\"No\"))", a_now, None]
    for c, v in enumerate(vals, 1):
        cell = ws.cell(row, c, v)
        cell.font, cell.border = f_body, box
    for c in (7, 11):
        ws.cell(row, c).fill, ws.cell(row, c).font = fill_input, f_input
last = first + len(top) - 1

for c in range(1, 12):
    for row in range(ex, last + 1):
        fmt = {4: "0%", 5: "0%", 6: "#,##0.###", 7: "#,##0.###", 8: "+0.0%;-0.0%;0.0%", 10: "#,##0.####"}.get(c)
        if fmt:
            ws.cell(row, c).number_format = fmt
        if c in (1, 4, 5, 9):
            ws.cell(row, c).alignment = Alignment(horizontal="center", vertical="center")
green, red = PatternFill("solid", fgColor="C6EFCE"), PatternFill("solid", fgColor="FFC7CE")
ws.conditional_formatting.add(f"I{first}:I{last}", CellIsRule(operator="equal", formula=['"Yes"'], fill=green))
ws.conditional_formatting.add(f"I{first}:I{last}", CellIsRule(operator="equal", formula=['"No"'], fill=red))

# summary (formulas over the 20 real rows only)
s0 = last + 2
summary = [
    ("Pets checked so far", f"=COUNT(G{first}:G{last})", "0"),
    ("Rose 2%+", f"=COUNTIF(I{first}:I{last},\"Yes\")", "0"),
    ("Hit rate (rose 2%+ / checked)", f"=IF(F{s0}=0,\"\",F{s0 + 1}/F{s0})", "0%"),
    ("Average change of the pets checked", f"=IF(F{s0}=0,\"\",AVERAGE(H{first}:H{last}))", "+0.0%;-0.0%;0.0%"),
    ("Average chance the model gave them", f"=AVERAGE(D{first}:D{last})", "0%"),
    ("Earlier 7-day tests: \"likely up\" calls that rose 2%+", 0.48, "0%"),
]
for j, (label, f, nf) in enumerate(summary):
    a, b = ws.cell(s0 + j, 2, label), ws.cell(s0 + j, 6, f)
    ws.merge_cells(start_row=s0 + j, start_column=2, end_row=s0 + j, end_column=5)
    a.font, b.font, b.number_format = f_bold, f_body, nf
    b.alignment = Alignment(horizontal="right")
ws.cell(s0 + 5, 6).font = f_input
ws.cell(s0 + 5, 6).comment = Comment("Hardcoded: up precision of gradient boosting with offer features, 7-day horizon, 19 test months "
                                     "(2025-05 to 2026-11), results/ads_model.md in the repo. A model saying 'up' is right about half the time.", "model")
ws.cell(s0 + 6, 1, "The chances are the model's own estimate for each pet; the hit rate of the top 20 is usually lower than their average "
                   "chance, because the model is over-confident on the pets it ranks highest. One week of 20 pets is a small sample.").font = f_note
ws.merge_cells(start_row=s0 + 6, start_column=1, end_row=s0 + 6, end_column=11)
ws.cell(s0 + 6, 1).alignment = Alignment(wrap_text=True)
ws.row_dimensions[s0 + 6].height = 26

widths = [7, 22, 17, 14, 14, 14, 16, 10, 10, 14, 30]
for c, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(c)].width = w
ws.freeze_panes = ws.cell(HR + 1, 3)

# ---- sheet 2: every form's current value on both lists ----
v2 = wb.create_sheet("Values now")
snap = json.loads((ROOT / "site" / "data.json").read_text(encoding="utf-8"))
v2["A1"] = (f"Values of the 20 pets in every form, on both lists, when this sheet was made (Elvebredd checked {snap['elve_at'][:10]} {snap['elve_at'][11:13]}:{snap['elve_at'][13:15]} UTC, "
            f"AMVGG {snap['amvgg_at'][:10]} {snap['amvgg_at'][11:13]}:{snap['amvgg_at'][13:15]} UTC). These can already differ from column F on the first sheet, which is the value on {asof}.")
v2["A1"].font = Font(name=ARIAL, size=12, bold=True)
v2["A2"] = ("AMVGG lists separate fly / ride / no-potion values for only a few pets; for the rest it calculates them from the fly ride value, "
            "as its own site does. A dash means the list has no value for that form.")
v2["A2"].font = f_note
hdr = ["Rank", "Pet", "Variant predicted"] + [f"Elve {form_name(k)}" for k in FORMS] + [f"AMVGG {form_name(k)}" for k in FORMS]
for c, t in enumerate(hdr, 1):
    cell = v2.cell(4, c, t)
    cell.font, cell.fill, cell.border = f_head, fill_head, box
    cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
v2.row_dimensions[4].height = 44
for i, r in enumerate(top):
    it = site.get(item_key(r["name"]), {})
    vals = [i + 1, r["name"], form_name(KEY[r["label"]])] + [(it.get("E") or {}).get(k) for k in FORMS] + [(it.get("A") or {}).get(k) for k in FORMS]
    for c, v in enumerate(vals, 1):
        cell = v2.cell(5 + i, c, "-" if v is None and c > 3 else v)
        cell.font, cell.border = f_body, box
        if c > 3:
            cell.number_format = "#,##0.####"
            cell.alignment = Alignment(horizontal="right")
for c in range(1, len(hdr) + 1):
    v2.column_dimensions[get_column_letter(c)].width = 22 if c == 2 else 7 if c == 1 else 16 if c == 3 else 11
v2.freeze_panes = "D5"

OUT.mkdir(exist_ok=True)
path = OUT / f"top20_rise_7d_{asof}.xlsx"
wb.save(path)
print(path)
for r in top[:5]:
    print(r["name"], r["label"], r["p_up"], r["value"])
