"""S1a throwaway: score takes against the doctor's enrollment, run phases A/B + candidate voices + commit (spec §6.4),
compare with hand labels, and print score distributions to pick thresholds. Usage:
  python s1a_analyze.py --enroll 'fixtures/audio/X/doctor_enroll_*.wav' --takes fixtures/audio/X/script_take1.wav ... [--min-speech 15]"""
import argparse, glob, json, pathlib
import numpy as np, soundfile as sf, torch
from silero_vad import load_silero_vad, get_speech_timestamps
from speechbrain.inference.speaker import EncoderClassifier

SR = 16000
ap = argparse.ArgumentParser()
ap.add_argument("--enroll", required=True); ap.add_argument("--takes", nargs="+", required=True)
ap.add_argument("--min-speech", type=float, default=15.0)
ap.add_argument("--tau-D-solo", type=float, default=0.60); ap.add_argument("--tau-notD", type=float, default=0.30)
ap.add_argument("--tau-D", type=float, default=0.55); ap.add_argument("--tau-P", type=float, default=0.50)
ap.add_argument("--m", type=float, default=0.20); ap.add_argument("--tau-same", type=float, default=0.55)
ap.add_argument("--learn-seconds", type=float, default=6.0); ap.add_argument("--reply-window", type=float, default=2.0)
a = ap.parse_args()

enc = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir=str(pathlib.Path.home() / ".cache/earshot-ecapa"))
vad = load_silero_vad()
def emb(x):
    with torch.no_grad():
        e = enc.encode_batch(torch.from_numpy(x).float().unsqueeze(0)).squeeze().numpy()
    return e / np.linalg.norm(e)
def cos(u, v): return float(np.dot(u, v))
def segments(x):
    ts = get_speech_timestamps(torch.from_numpy(x).float(), vad, sampling_rate=SR, min_silence_duration_ms=600, min_speech_duration_ms=250, return_seconds=True)
    return [(t["start"], t["end"]) for t in ts]

# --- doctor enrollment + quality check (one voice: every 1.5 s window close to the clip mean)
doc = []
for f in sorted(glob.glob(a.enroll)):
    x, _ = sf.read(f, dtype="float32"); speech = sum(e - s for s, e in segments(x))
    e = emb(x); wins = [emb(x[i:i + int(1.5 * SR)]) for i in range(0, len(x) - int(1.5 * SR), int(0.75 * SR))]
    cons = min(cos(w, e) for w in wins)
    print(f"enroll {pathlib.Path(f).name}: speech {speech:.1f}s, min window cos {cons:.2f} {'OK' if speech >= a.min_speech else 'TOO SHORT'}")
    doc.append(e)

def truth_of(s, e, labels):
    best, ov = "SILENCE", 0.0
    for l in labels:
        o = min(e, l["end"]) - max(s, l["start"])
        if o > ov: best, ov = l["speaker"], o
    return best

allstats = {"doc_sD": [], "non_sD": [], "pat_margin": [], "doc_margin": []}
for take in a.takes:
    x, _ = sf.read(take, dtype="float32"); labels = json.loads(pathlib.Path(take).with_suffix(".labels.json").read_text())
    cands, patient, prev_doc_end, rows, doctor_turns = {}, None, None, [], 0
    for s, e in segments(x):
        seg = x[int(s * SR):int(e * SR)]; d = e - s; t = truth_of(s, e, labels); v = emb(seg)
        sD = max(cos(v, k) for k in doc); sP = max(cos(v, k) for k in patient) if patient else None
        relabels = []
        if d < 1.0: lab = "UNCERTAIN"
        elif patient is None:  # phase A
            if sD >= a.tau_D_solo: lab = "DOCTOR"
            elif sD <= a.tau_notD:
                lab = "PATIENT?"; reply = prev_doc_end is not None and s - prev_doc_end <= a.reply_window
                cid = next((c for c, cd in cands.items() if cos(v, cd["centroid"]) >= a.tau_same), None)
                if cid is None: cid = "ABCDEFG"[len(cands)]; cands[cid] = {"embs": [], "secs": 0.0, "replies": 0, "rows": []}
                c = cands[cid]; c["embs"].append(v); c["secs"] += d; c["replies"] += int(reply); c["rows"].append(len(rows))
                c["centroid"] = np.mean(c["embs"], 0); c["centroid"] /= np.linalg.norm(c["centroid"])
                ok = [k for k, cd in cands.items() if cd["secs"] >= a.learn_seconds and cd["replies"] >= 1]
                if ok:
                    win = max(ok, key=lambda k: (cands[k]["replies"], cands[k]["secs"])); patient = list(cands[win]["embs"])
                    relabels = [k for k in cands if k != win]
                    print(f"  commit -> candidate {win} at {e:.1f}s ({cands[win]['secs']:.1f}s, {cands[win]['replies']} replies); relabelled OTHER: {relabels}")
            else: lab = "UNCERTAIN"
        else:  # phase B
            if sD >= a.tau_D and sD - sP >= a.m: lab = "DOCTOR"
            elif sP >= a.tau_P and sP - sD >= a.m: lab = "PATIENT"
            else: lab = "UNCERTAIN"
        if lab == "DOCTOR": prev_doc_end = e; doctor_turns += 1
        rows.append({"s": s, "d": d, "truth": t, "sD": sD, "sP": sP, "label": lab})
        if patient is not None and lab == "PATIENT?":  # commit happened on this segment: relabel every candidate row
            for k, cd in cands.items():
                for r in cd["rows"]: rows[r]["label"] = "PATIENT" if k == win else "OTHER"
            cands = {}  # phase B from now on
        (allstats["doc_sD"] if t == "DOCTOR" else allstats["non_sD"]).append(sD)
        if sP is not None: (allstats["doc_margin"] if t == "DOCTOR" else allstats["pat_margin"]).append((sD - sP) if t == "DOCTOR" else (sP - sD))
    print(f"\n== {pathlib.Path(take).name}")
    exp = {"DOCTOR": "DOCTOR", "PATIENT": "PATIENT", "OTHER": "OTHER"}
    good = bad_pd = 0
    for r in rows:
        lab = r["label"].rstrip("?"); flag = "ok" if lab == exp.get(r["truth"]) else ("UNCERTAIN" if lab == "UNCERTAIN" else "WRONG")
        if r["truth"] != "DOCTOR" and lab == "DOCTOR": bad_pd += 1
        good += flag == "ok"
        print(f"  {r['s']:6.1f}s {r['d']:4.1f}s truth={r['truth']:<7} sD={r['sD']:.2f} sP={'-' if r['sP'] is None else f'{r['sP']:.2f}'} -> {r['label']:<9} {flag}")
    in_cand = sum(1 for r in rows if r["truth"] == "DOCTOR" and r["label"] in ("PATIENT", "PATIENT?", "OTHER"))
    print(f"  correct {good}/{len(rows)} · non-doctor labelled DOCTOR: {bad_pd} · doctor segments in a candidate: {in_cand} · patient learned: {patient is not None}")

def q(xs): return "n=0" if not xs else f"n={len(xs)} min={min(xs):.2f} p10={np.percentile(xs,10):.2f} med={np.median(xs):.2f} p90={np.percentile(xs,90):.2f} max={max(xs):.2f}"
print("\n== score distributions (pick thresholds with a safety gap)")
print("  s_D on DOCTOR segments     ", q(allstats["doc_sD"]))
print("  s_D on non-doctor segments ", q(allstats["non_sD"]))
print("  phase B margin, doctor (sD-sP) ", q(allstats["doc_margin"]))
print("  phase B margin, patient (sP-sD)", q(allstats["pat_margin"]))
