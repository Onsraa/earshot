# Earshot: infrastructure and runbook

## 1. Machine and environment
- **Demo machine:** an Apple Silicon Mac. Tested on an M4 Pro with 24 GB of RAM. Use the same Mac for enrollment, rehearsals and the demo, because the voice thresholds depend on the microphone.
- **Python 3.12, managed with `uv`.** Every library below was verified on 3.12. The Mac's default Python 3.14 is **not** tested with these libraries, so don't use it.
- **System tool:** `ffmpeg` (Homebrew), for audio conversion and for the synthetic test voices.

### Dependencies (versions verified together on 2026-10-06)
```toml
# pyproject.toml (written at hour 0, Task 1)
[project]
name = "earshot"
requires-python = ">=3.12,<3.13"
dependencies = [
  "fastapi==0.142.2", "uvicorn==0.54.0", "httpx==0.28.1",
  "numpy==2.5.3", "soundfile==0.14.0", "sounddevice==0.5.6",
  "torch==2.14.1", "torchaudio==2.11.0", "speechbrain==1.1.1", "silero-vad==6.2.3",
  "mistralai==3.0.0", "text2num==3.1.0",
]
[project.optional-dependencies]
tier2 = ["pyannote.audio==4.0.7", "edsnlp==0.23.0"]
dev = ["pytest==9.1.1", "pytest-asyncio==1.4.0"]
[tool.pytest.ini_options]
asyncio_mode = "auto"
```
- **Whisper fallback:** add `mlx-whisper` (or `faster-whisper`) at hour 0 **after checking which one installs** on 3.12/arm64. It isn't verified yet.
- **YAMNet (Tier 3):** choose the runtime in S6. Don't add it before then.

## 2. Secrets
`earshot/.env` is git-ignored and loaded at startup (for example with `set -a; source .env; set +a`):
```
MISTRAL_API_KEY=…      # Voxtral + Mistral Large
JEV_API_KEY=…          # TypeSafe Jev
HF_TOKEN=…             # Tier 2–3 only: pyannote segmentation, WeSpeaker; accept the model conditions on huggingface.co first
# AWS_PROFILE=…        # only if the scribe runs on Claude via Bedrock
```
Never commit keys. Never paste them into prompts, logs or the audit trail.

## 3. Models and data to download before the event
| What | How | Where it ends up |
|---|---|---|
| ECAPA | the first `EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir=~/.cache/earshot-ecapa)` call downloads it | `~/.cache/earshot-ecapa` (✓ already there from the dry run) |
| Silero VAD | ships inside the pip package | site-packages |
| pyannote segmentation-3.0 (Tier 2) | accept its conditions on Hugging Face, then `Model.from_pretrained(..., token=HF_TOKEN)` once | HF cache |
| Whisper fallback | download the model once on venue-independent wifi | HF or mlx cache |
| BDPM, RCP | done (S8) | `reference/` |
| Offline answers | recorded during rehearsals (Task 16) | `fixtures/cache/` |

**The day before:** run a full offline replay with **wifi turned off** to prove nothing is missing from the cache.

## 4. Network
- The venue wifi is unknown (S7). Bring a **phone hotspot** as a backup.
- If the network is unreliable, the demo runs in **offline mode**: the rehearsal recording is replayed with the answers cached during rehearsal (spec §6.13). Decide in the morning which mode to use, based on how the wifi behaves.

## 5. Cost (order of magnitude)
| Service | Price | One demo run (about 75 s of audio, 8 sentences) |
|---|---|---|
| Voxtral Mini Transcribe 2 | $0.003 per minute (Mistral, February 2026) | ≈ $0.004 |
| Jev | $0.042 per million input tokens, output free (Jev launch notes, `../../docs/ideas.md`) | well under $0.01 |
| Mistral Large (scribe ×~4 runs + fallbacks) | check current prices in the Mistral console | about a few cents |

Plan for about **50 rehearsals plus the tests**. The total should stay well under €20, but **check the console after Phase 0**.

## 6. Hardware checklist (bring on 10 October)
- The demo Mac and its charger, plus an extension lead.
- The video adapter for the projector (HDMI or USB-C; ask about the connector in S7).
- **The fallback:** 2 lapel microphones and a USB stereo audio interface or adapter, to run spec §6.1 if S1a or the venue fails.
- Headphones, to check recordings.
- A phone with the TV clip and a small speaker (Tier 3 bonus).
- A phone hotspot.

## 7. Runbook

### Hour 0 at the event (both developers, about 30 min, inside Task 1)
```bash
git switch -c earshot-build              # from main; phase-0 data is merged or copied in
cd earshot && uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e ".[dev]"
set -a; source .env; set +a
.venv/bin/python -c "import torch, speechbrain, silero_vad, mistralai, fastapi; print('ok')"
cp <values from docs/test-results.md> config/thresholds.json   # and config/models.json (architecture.md §6)
```
**Then record the doctor's voice again at the demo spot, if it has moved** (spec A19).

### Starting the demo
```bash
cd earshot && set -a; source .env; set +a
.venv/bin/uvicorn earshot.server:app --port 8000      # open http://localhost:8000 on the projector, full screen
```
1. Check every status light is green, `médecin ✓` shows, and the patient is `en attente` (waiting).
2. `POST /start {"source":"mic"}`. In offline mode, use `{"source":"wav","path":"fixtures/audio/demo_rehearsal.wav"}` instead.
3. Play the scene. Press `E` to reveal the verdicts.
4. In Tier 2: « Fin de consultation », the corrections, then « Signer ».
5. `POST /reset` between runs. The doctor's voice is kept.

### Falling back, in order
1. Live microphone.
2. Replay of the WAV recording.
3. `POST /mode {"mode":"offline"}` plus the WAV.
4. The backup video, kept open in a browser tab.

Switching takes under 10 seconds. Rehearse it.

### Code freeze
At hour 32: `git tag demo-freeze`. After that, only change configuration (thresholds), never code.

## 8. Repository hygiene
- `main` holds the docs and the Phase 0 data. Phase 0 work is on `earshot-phase0`; merge it before the event.
- The event build happens on `earshot-build`, with one commit per task (as `plan.md` specifies).
- `spikes/` is deleted at the end of Phase 0: `git rm -r earshot/spikes`. Keep its results, already recorded in `test-results.md`.
- Audio files (`*.wav`) stay out of git, because they contain biometric data.
