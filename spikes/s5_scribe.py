"""S5 throwaway: run the naive scribe prompt (docs/prompts.md) on the §7.10 script 10x; count the realistic errors
(ibuprofen as a prescription, sick leave 3 days, blood test as prescribed) and identity churn. Needs MISTRAL_API_KEY."""
import json, os, pathlib, re, sys, collections
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from s1a_synth import SCRIPT
from mistralai.client import Mistral
root = pathlib.Path(__file__).resolve().parents[1]
prompt = re.search(r"```\n(Tu es un assistant.*?)```", (root / "docs/prompts.md").read_text(), re.S).group(1)
order, transcript = {}, []
for spk, text in SCRIPT:
    order.setdefault(spk, len(order) + 1); transcript.append(f"Locuteur {order[spk]} : {text}")
c = Mistral(api_key=os.environ["MISTRAL_API_KEY"]); errs, keys_seen = collections.Counter(), []
for run in range(10):
    m = c.chat.complete(model=os.environ.get("SCRIBE_MODEL", "mistral-large-latest"), response_format={"type": "json_object"},
                        messages=[{"role": "system", "content": prompt}, {"role": "user", "content": "\n".join(transcript)}])
    note = json.loads(m.choices[0].message.content); acts = note.get("actions", [])
    blob = json.dumps(acts, ensure_ascii=False).lower()
    errs["ibuprofen_as_action"] += "ibupro" in blob
    errs["sick_leave_3_days"] += any(a.get("type") == "sick_leave" and re.search(r"\b3\b|trois", json.dumps(a, ensure_ascii=False)) for a in acts)
    errs["blood_test_as_action"] += "prise de sang" in blob
    keys_seen.append(sorted({(a.get("type"), str(a.get("target", "")).lower()) for a in acts}))
    print(f"run {run}: {[(a.get('type'), a.get('target'), a.get('fields')) for a in acts]}")
print("errors over 10 runs:", dict(errs)); print("distinct action sets:", len({json.dumps(k) for k in keys_seen}))
