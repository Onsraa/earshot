"""S1a throwaway: record the doctor's enrollment clips and the takes on the DEMO Mac + mic, with auto draft labels.
  python s1a_record.py enroll --out fixtures/audio/real --n 3 --seconds 25
  python s1a_record.py take   --out fixtures/audio/real --name script_take1 --seconds 90 [--tv-first]
Draft labels map VAD segments to script lines in order; CHECK and fix `*.labels.json` by hand (speaker per segment)."""
import argparse, json, pathlib, time
import numpy as np, sounddevice as sd, soundfile as sf, torch
from silero_vad import load_silero_vad, get_speech_timestamps
from s1a_synth import SCRIPT, ENROLL, TV

SR = 16000
ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["enroll", "take"])
ap.add_argument("--out", required=True); ap.add_argument("--n", type=int, default=3); ap.add_argument("--seconds", type=float, default=25)
ap.add_argument("--name", default="script_take1"); ap.add_argument("--tv-first", action="store_true")
a = ap.parse_args(); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)

def rec(seconds):
    for i in (3, 2, 1): print(f"  … {i}"); time.sleep(1)
    print("  ● RECORDING"); x = sd.rec(int(seconds * SR), samplerate=SR, channels=1, dtype="float32"); sd.wait(); print("  ■ stop")
    return x[:, 0]

if a.mode == "enroll":
    for i in range(1, a.n + 1):
        print(f"\nDoctor, clip {i}/{a.n}: read this aloud, calmly, at your demo position:\n\n  {ENROLL[(i - 1) % len(ENROLL)]}\n")
        input("Press Enter to start…"); sf.write(out / f"doctor_enroll_{i}.wav", rec(a.seconds), SR)
else:
    lines = ([TV] if a.tv_first else []) + SCRIPT
    print("\nScript (leave ~1 s between turns; the TV line is played from a phone):\n")
    for spk, text in lines: print(f"  [{spk}] {text}")
    input("\nPress Enter to start…"); x = rec(a.seconds); sf.write(out / f"{a.name}.wav", x, SR)
    ts = get_speech_timestamps(torch.from_numpy(x), load_silero_vad(), sampling_rate=SR, min_silence_duration_ms=600, min_speech_duration_ms=250, return_seconds=True)
    labels = [{"start": t["start"], "end": t["end"], "speaker": lines[i][0] if len(ts) == len(lines) else "?", "text": lines[i][1] if len(ts) == len(lines) and i < len(lines) else ""} for i, t in enumerate(ts)]
    (out / f"{a.name}.labels.json").write_text(json.dumps(labels, ensure_ascii=False, indent=1))
    print(f"{len(ts)} segments for {len(lines)} script lines → labels {'auto-mapped' if len(ts) == len(lines) else 'need manual speakers (?)'}: {a.name}.labels.json")
