"""S8 throwaway: what do text2num, dateparser and EDS-NLP do with the phrase set? Prints a table; no product logic."""
import json, pathlib, datetime as dt
from text_to_num import alpha2digit
import dateparser
import edsnlp, edsnlp.pipes as eds

root = pathlib.Path(__file__).resolve().parents[1]
data = json.loads((root / "fixtures/normalizer_phrases.json").read_text())
base = dt.datetime(2026, 10, 10, 12, 0)
nlp = edsnlp.blank("eds")
nlp.add_pipe(eds.dates())
for p in data["phrases"]:
    t = p["text"]
    a2d = alpha2digit(t, "fr", threshold=0)
    dp = dateparser.parse(t, languages=["fr"], settings={"RELATIVE_BASE": base, "PREFER_DATES_FROM": "future"})
    doc = nlp(t)
    eds_dates = [(s.text, str(getattr(s._, "date", None))) for s in doc.spans.get("dates", [])]
    eds_dur = [(s.text, str(getattr(s._, "duration", None))) for s in doc.spans.get("durations", [])]
    print(f"{p['id']:>2} | {t} | text2num: {a2d} | dateparser: {dp.date() if dp else None} | eds dates: {eds_dates} | eds durations: {eds_dur}")
