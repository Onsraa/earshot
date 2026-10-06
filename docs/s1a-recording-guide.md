# S1a recording session (about 1 h, both actors)

**Goal:** prove, on the **demo Mac and microphone**, that Earshot labels every sentence correctly. That means it learns the patient's voice from their first answer, and never labels the patient, or a TV, as the doctor (spec §6.4, §12).

## Setup
- **Place:** as close as possible to stage conditions. Ideally the venue; otherwise a room with similar noise.
- **Position:** the Mac between the two actors, about 50 cm from each. Use the same positions you'll use on stage.
- **Background:** no music. Once the script takes are done, record the noisy take described below.
- **Software:**

  ```bash
  cd earshot
  uv venv --python 3.12 spikes/.venv
  uv pip install --python spikes/.venv/bin/python torch torchaudio speechbrain silero-vad soundfile numpy sounddevice
  ```

## 1. Record the doctor's voice once (5 min)
```bash
spikes/.venv/bin/python spikes/s1a_record.py enroll --out fixtures/audio/real --n 3 --seconds 25
```
The doctor-actor reads each text aloud at their demo position.

## 2. Script takes (20 min)
1. **Script takes** (lines 1–8, spec §7.10). Repeat 5 times, `--name script_take1` to `script_take5`. Leave about 1 s between turns, and keep each line at least 1.5 s long.
   ```bash
   spikes/.venv/bin/python spikes/s1a_record.py take --out fixtures/audio/real --name script_take1 --seconds 90
   ```
2. **TV take** (spec L7). Before line 1, the patient-actor plays the TV clip on a phone at normal TV volume. Use a **male** voice if the doctor-actor is a man, so it's a hard case. Any French news or ad clip of about 6 s works.
   ```bash
   spikes/.venv/bin/python spikes/s1a_record.py take --out fixtures/audio/real --name tv_first_take --seconds 100 --tv-first
   ```
3. **Free conversation** (3 min). Improvise a consultation with natural back-and-forth: `--name free_take --seconds 180`.
4. **Check the labels.** If the tool says "need manual speakers (?)", open `fixtures/audio/real/<name>.labels.json` and set each `speaker` to DOCTOR, PATIENT or OTHER, listening to the WAV.

## 3. Analyse (10 min)
```bash
spikes/.venv/bin/python spikes/s1a_analyze.py --enroll 'fixtures/audio/real/doctor_enroll_*.wav' \
  --takes fixtures/audio/real/script_take*.wav fixtures/audio/real/tv_first_take.wav fixtures/audio/real/free_take.wav
```
- **Read the score distributions** printed at the end, then pick thresholds with a safety gap:
  - **`--tau-D-solo`:** above the highest doctor score (s_D) of any non-doctor segment;
  - **`--tau-notD`:** below the lowest doctor score of any doctor segment, and above most patient segments;
  - **`--tau-same`:** the threshold for grouping segments into the same voice;
  - **`--m`:** the margin between the doctor and patient scores in phase B.
- **Re-run with those values until:**
  - every scripted line is `ok`;
  - `non-doctor labelled DOCTOR: 0`;
  - `doctor segments in a candidate: 0`;
  - in the TV take, the commit picks the patient and relabels the TV as OTHER.
- **Try `--learn-seconds 4`, then `6`, then `8`.** Keep the smallest that still passes.
- **Write the numbers in `docs/test-results.md` (S1a).**

## If it fails
1. Re-record the doctor's voice at the exact demo position.
2. Move the Mac closer to the doctor's position and the patient's position.
3. Try the WeSpeaker model. It needs a Hugging Face token; ask Claude to add it to the script.
4. **Last resort:** one lapel mic per person (spec §6.1).

**Note from the synthetic dry run** (2026-10-06, macOS voices, plumbing only): it ran end to end, with 8/8 and 9/9 correct on the synthetic takes, and the TV take was relabelled correctly. On macOS, the voices "Jacques" and "Eddy" are the same synthetic voice (similarity 0.99), so never use one of them as a "different" person in tests.
