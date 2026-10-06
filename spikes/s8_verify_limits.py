"""S8 throwaway: check every limit number appears verbatim in its quote and in the cached RCP section."""
import json, re, sys, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
data = json.loads((root / "reference/drug_limits.json").read_text())
sections = {p.name.split("_")[0]: p.read_text() for p in (root / "reference/rcp").glob("*_4.2.txt")}
ok = True
for sub, lim in data.items():
    if sub.startswith("_"):
        continue
    quote = lim["quote"]
    for part in [q.strip() for q in quote.split("…")]:
        if part and part not in sections.get(sub, ""):
            ok = False; print(f"FAIL {sub}: quote part not in RCP section: {part[:60]}…")
    nums = set(re.findall(r"\d+", quote.replace(" ", "")))
    for field in ("usual_daily_mg", "max_daily_mg", "max_per_intake_mg", "min_interval_h"):
        v = lim.get(field)
        if v is not None and str(v) not in nums:
            ok = False; print(f"FAIL {sub}.{field}={v} not in quote")
    print(f"{sub}: checked")
print("ALL OK" if ok else "FAILURES"); sys.exit(0 if ok else 1)
