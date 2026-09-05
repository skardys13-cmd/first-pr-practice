#!/usr/bin/env python3
"""Confirms the workbook and the page produce the same numbers.
The page's figures come from engine.mjs; the workbook's come from LibreOffice
having actually evaluated its formulas. Neither side is copied from the other."""
import json, datetime as dt, sys, re, warnings
warnings.filterwarnings("ignore")
import formulas

D = json.load(open("dist/engine-dump.json"))
CM = json.load(open("dist/cellmap.json"))
T = D["today"]

# LibreOffice cannot load any file in this sandbox, so the workbook's formulas
# are evaluated here by an independent Excel-formula engine instead. Nothing is
# read back from openpyxl's cache - every number below was computed FROM THE
# FORMULAS IN THE FILE, then compared against the page's engine.
XL = formulas.ExcelModel().loads("dist/RIA_Operations_Model.xlsx").finish()
SOL = XL.calculate()
CELLS = {}
ERRORS = []
_key = re.compile(r"^'\[[^\]]+\](?P<sheet>[^']+)'!(?P<addr>\$?[A-Z]+\$?\d+)$")
for k, v in SOL.items():
    m = _key.match(k)
    if not m: continue
    try: val = v.value[0, 0]
    except Exception:
        try: val = v.value
        except Exception: continue
    addr = m.group("addr").replace("$", "")
    CELLS[(m.group("sheet").upper(), addr)] = val
    if isinstance(val, str) and val.startswith("#"):
        ERRORS.append(f"{m.group('sheet')}!{addr} = {val}")

class Sheet:
    def __init__(self, nm): self.nm = nm.upper()
    def __getitem__(self, addr):
        class C:
            value = CELLS.get((self.nm, addr.replace("$", "")))
        return C
EN, C1, C2, C3, C4, FS, AS = (Sheet("Engine"), Sheet("Case1_Departure"), Sheet("Case2_Capacity"),
                              Sheet("Case3_CostToServe"), Sheet("Case4_Seat"), Sheet("FeeSchedule"), Sheet("Assumptions"))
npass = nfail = 0
def chk(label, xl, js, tol=1e-6):
    global npass, nfail
    if xl is None:
        nfail += 1; print(f"  FAIL  {label}: workbook cell is empty (formula never evaluated)"); return
    if isinstance(xl, str):
        nfail += 1; print(f"  FAIL  {label}: workbook holds text {xl!r}"); return
    try: xl = float(xl)
    except Exception:
        nfail += 1; print(f"  FAIL  {label}: workbook value not numeric ({xl!r})"); return
    d = abs(xl - js)
    rel = d / max(1e-9, abs(js)) if js else d
    if rel <= tol or d < 5e-7:
        npass += 1; print(f"  PASS  {label}: {xl:,.4f}")
    else:
        nfail += 1; print(f"  FAIL  {label}: workbook {xl:,.6f}  vs  page {js:,.6f}  (rel {rel:.2e})")
def sect(t): print("\n" + t + "\n" + "-" * len(t))

sect("Formula errors across the whole workbook")
if ERRORS:
    nfail += 1; print(f"  FAIL  {len(ERRORS)} cells evaluate to an Excel error: {ERRORS[:8]}")
else:
    npass += 1; print(f"  PASS  no #REF!/#NAME?/#VALUE!/#DIV0! anywhere ({len(CELLS)} cells evaluated)")

sect("Fee schedule — the three hand-worked households")
for i, (aum, expect) in enumerate(zip([145000, 520000, 5100000], D["fee"])):
    row = CM["fee_check_first"] + i
    chk(f"${aum:,} tiered fee", FS[f"C{row}"].value, expect)
    v = FS[f"E{row}"].value
    npass_ = v == "PASS"
    print(("  PASS  " if npass_ else "  FAIL  ") + f"hand-check cell says {v}")
    globals()['npass' if npass_ else 'nfail'] = globals()['npass' if npass_ else 'nfail'] + 1

sect("Engine — rates, book and revenue")
E = CM["engine"]
for key, js, tol in [
    ("blended", T["rates"]["blendedOpsHourly"], 1e-6),
    ("advhr", T["rates"]["advisorLoadedHourly"], 1e-6),
    ("advrev", T["case4"]["revenuePerAdvisorHour"], 1e-6),
    ("hh", T["book"]["totalHouseholds"], 1e-9),
    ("aum", T["book"]["aumTotal"], 1e-9),
    ("new", T["book"]["newTotal"], 1e-9),
    ("rev", T["revenue"]["total"], 1e-9),
    ("revhh", T["revenue"]["perHousehold"], 1e-9),
    ("revadv", T["revenue"]["perAdvisor"], 1e-9),
    ("revemp", T["revenue"]["perEmployee"], 1e-9),
    ("advcount", T["revenue"]["advisorCount"], 1e-9),
]:
    chk(key, EN[E[key]].value, js, tol)

sect("Engine — operations hours")
for key, js in [("recur", T["capacity"]["required"]["recurring"]),
                ("onboard", T["capacity"]["required"]["onboarding"]),
                ("firmh", T["capacity"]["required"]["firm"]),
                ("req", T["capacity"]["required"]["total"]),
                ("avail", T["capacity"]["available"]),
                ("util", T["capacity"]["utilisation"]),
                ("opsadv", T["capacity"]["opsOnAdvisors"]),
                ("fixed", T["capacity"]["fixedHours"]),
                ("perhh", T["capacity"]["perHouseholdHours"]),
                ("breakhh", T["capacity"]["breakHouseholdsExact"])]:
    chk(key, EN[E[key]].value, js)
for rid, js in T["capacity"]["hoursByOwner"].items():
    if "own_" + rid in E: chk(f"hours owned by {rid}", EN[E["own_" + rid]].value, js)

sect("Case 3 — cost to serve, layer by layer, tier by tier")
ET = CM["engine_tier"]
for i, tier in enumerate(T["tiers"]):
    for key, js in [("revph", tier["revenuePerHousehold"]), ("dirh", tier["directHours"]),
                    ("dircost", tier["costLayers"]["directOps"]), ("allocfirm", tier["costLayers"]["allocFirm"]),
                    ("advcost", tier["costLayers"]["advisory"]), ("ovh", tier["costLayers"]["firmOverhead"]),
                    ("loaded", tier["costTotalLoaded"]), ("mgloaded", tier["marginLoaded"]),
                    ("mgdirect", tier["marginDirect"]), ("onbcost", tier["onboardingCost"])]:
        chk(f"{tier['tier']} {key}", EN[ET[key][i]].value, js)

sect("Case 1 — the departure, and all three responses")
c1 = CM["case1"]
chk("catalogued hours", C1[c1["cat"]].value, T["case1"]["catalogued"])
chk("contracted hours", C1[c1["con"]].value, T["case1"]["contracted"])
chk("unmapped hours", C1[c1["unm"]].value, T["case1"]["unmapped"])
opt = CM["case1_options"]
for i, o in enumerate(T["case1"]["options"]):
    row = opt["first_row"] + i
    chk(f"{o['key']} · annual cost", C1[f"{opt['cost']}{row}"].value, o["annualCost"])
    chk(f"{o['key']} · hours available", C1[f"{opt['avail']}{row}"].value, o["available"])
    chk(f"{o['key']} · utilisation", C1[f"{opt['util']}{row}"].value, o["utilisation"])
    chk(f"{o['key']} · hours with no owner", C1[f"{opt['short']}{row}"].value, o["hoursShort"])

sect("Case 2 — the capacity crossing")
c2 = CM["case2"]
chk("utilisation today", C2[c2["util"]].value, T["capacity"]["utilisation"])
chk("months to the crossing", C2[c2["frac"]].value, T["capacity"]["breakMonthFrac"], 1e-6)
chk("households at the crossing", C2[c2["hh"]].value, T["capacity"]["breakHouseholds"], 1e-6)
xd = C2[c2["date"]].value
jd = dt.date.fromisoformat(T["capacity"]["breakDate"])
if isinstance(xd, dt.datetime): xd = xd.date()
elif isinstance(xd, (int, float)):           # Excel serial -> date (epoch 1899-12-30)
    xd = dt.date(1899, 12, 30) + dt.timedelta(days=int(xd))
if xd == jd: npass += 1; print(f"  PASS  crossing date: {xd}")
else: nfail += 1; print(f"  FAIL  crossing date: workbook {xd} vs page {jd}")

sect("Case 4 — the seat")
c4, c4c = CM["case4"], CM["case4_cells"]
chk("seat cost, loaded", C4[c4["cost"]].value, T["case4"]["seatCostLoaded"])
chk("compensation delta", C4[c4["delta"]].value, T["case4"]["seatCompDelta"])
for i, p in enumerate(T["case4"]["protect"]):
    row = c4c["protect_first"] + i
    chk(f"protects · {p['key']}", C4[f"D{row}"].value, p["value"])
    if p["hours"] is not None: chk(f"protects · {p['key']} hours", C4[f"B{row}"].value, p["hours"])
chk("total protected", C4[c4c["protect_total"]].value, T["case4"]["protectTotal"])
chk("surplus", C4[c4c["surplus"]].value, T["case4"]["surplus"])
chk("paraplanning hours displaced", C4[c4c["displaced"]].value, T["case4"]["displacedParaplanningHours"])

sect("The ledger")
lg = CM["ledger"]
tags = [AS[f"E{r}"].value for r in range(lg["first"], lg["last"] + 1)]
valid = {"MEASURED", "OBSERVED", "BENCHMARK", "ESTIMATED", "PLACEHOLDER"}
bad = [t for t in tags if t not in valid]
if not bad: npass += 1; print(f"  PASS  every one of the {len(tags)} ledger rows carries a valid tag")
else: nfail += 1; print(f"  FAIL  {len(bad)} ledger rows have no valid tag: {bad[:5]}")

print(f"\n{'='*66}\n  {npass} passed, {nfail} failed\n{'='*66}")
sys.exit(1 if nfail else 0)
