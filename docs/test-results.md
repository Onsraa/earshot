# Phase 0 test results

Fill this in during the week. **The test code gets deleted. The recordings, `reference/` and this file are kept.** The values below go into `config/thresholds.json`, `config/models.json` and `reference/drug_limits.json` at the event.

Recordings go in `earshot/fixtures/audio/` (git-ignore them if they're large), each with a `.labels.json` file.

## S7: practical details (day 1)
- **Code written before the event allowed:**
- **Stage microphones required:**
- **Wifi:**
- **Length of the demo slot:**

## S1a: who is speaking, and learning the patient's voice (Tier 1, do first)
- **Date and location:**
- **Microphone and Mac:**
- **Doctor recording** (2–3 clips × 20–30 s): number of clips; quality check passed? `~/.earshot/doctor.npz` created?
- **Recordings:** 5 takes of the script; 3 minutes of free conversation; 1 take with the TV playing before line 2.
- **Models:**

  | Model | Script lines correct | Patient labelled DOCTOR | Doctor segments assigned to a candidate voice | Commit correct in the TV take | UNCERTAIN in free conversation |
  |---|---|---|---|---|---|
  | ECAPA | / | | | | |
  | WeSpeaker ResNet34 | / | | | | |

- **Speech needed to learn the patient's voice:** 4 s / 6 s / 8 s → results, and the chosen `learn_seconds`:
- **Chosen model:**
- **Thresholds:** `tau_D_solo =` · `tau_notD =` · `tau_D =` · `tau_P =` · `m =` · `tau_same =` · `tau_cons =` · `min_seconds = 1.0` · `reply_window_s = 2.0`
- **Score histograms** (path):
- **Verdict:** PASS / FAIL. If FAIL, the fix applied:
- **Synthetic dry run (2026-10-06): plumbing only, not accuracy.**
  - **Setup:** `spikes/s1a_synth.py` uses macOS voices: doctor = Jacques, patient = Flo (fr_FR), TV = Grandpa (fr_FR).
  - **Script:** `spikes/s1a_analyze.py` runs the steps from spec §6.4: VAD, ECAPA, phase A, candidate voices, commit, phase B.
  - **Results:**
    - script take: **8/8 correct**;
    - take with the TV speaking first: **9/9 correct**. The commit chose the voice that replied to the doctor (B) and relabelled the TV (A) as OTHER retroactively.
  - **Two things learned:**
    1. The default τ_notD of 0.30 was too strict for these voices, so the patient was never learned until it was raised. Thresholds *must* come from the real recordings.
    2. On macOS, "Jacques" and "Eddy" are **the same synthetic voice** (cosine 0.99). A first run that used Eddy as the "TV" therefore labelled it DOCTOR. That was a fault in the test setup, not a finding about Earshot. Never use them as two different people.
  - **Recording tool:** `spikes/s1a_record.py`. Not yet tested with a live microphone, because it needs the actors and the mic permission prompt.
  - **Session guide:** `docs/s1a-recording-guide.md`.

## S1b: difficult conditions (Tiers 2–3)
- **Conditions recorded:**
- **Variants A–E compared:**
- **Per-duration thresholds:**
- **Cohort of other voices** (path, number of clips):
- **Replayed and cloned voices:** they are expected to get through. Record what happened, as evidence for the documented limit.

## S2: speed
- **End of sentence → label + text, 90th percentile:** CPU · MPS

## S3: Voxtral
- **API, read 2026-10-06** (docs + the installed SDK, `mistralai` 3.0.0):
  - **Import:** `from mistralai.client import Mistral` (not `from mistralai import Mistral`).
  - **Call:** `client.audio.transcriptions.complete(model="voxtral-mini-latest", file={"content", "file_name"}, timestamp_granularities=["word"], context_bias=[≤100 terms], diarize=False, language=…)`.
  - **Response:** `TranscriptionResponse{model, text, usage, language, segments[]}`, where each segment is `{text, start, end, type, score, speaker_id}`.
  - **⚠ The docs say `timestamp_granularities` and `language` can't be used together.** With word timestamps on, the language is auto-detected, so S3 must check it comes out as French.
  - **Runner:** `spikes/s3_voxtral.py`. It's ready, but blocked until `MISTRAL_API_KEY` is set. It uses synthetic voices first; re-run it on real voices.
- **Endpoint and model:** · **Word timestamps:** yes / no · **Cost:**
- **Accuracy on 20 sentences,** with and without the drug-name hints:
- **Decision:**

## S4: the questions asked about each sentence
- **Jev API, read 2026-10-06** from docs.typesafe.ai/api:
  - **Request:** `POST https://api.typesafe.ai/v1/systemone`, header `Authorization: Bearer <key>`, body `{"state", "model": "jev-latest", "questions": {id: {type: "noul"|"choice"|"score", instructions, criteria}}}`.
  - **Answers:**
    - `noul` → `{"noul": 0–1}`;
    - `choice` → `{"choice", "probabilities", "confidence"}`;
    - `score` → `{"score", "legend", "probabilities", "confidence"}`.
  - **Errors:** 401, 422, 429 (back off and retry), 529.
  - **Not stated in the docs:** French support and token limits. S4 measures French.
  - The search results also mention a third-party endpoint (`tokenra.io/v1/decisions`). **Use the official one.**
- **Sentence set (kept):** `fixtures/questions_set.json`, 128 items:
  - Q2: 10 of each of the 7 kinds;
  - Q5: 16; Q4: 22; Q6: 14;
  - 6 adversarial items.
- **Wording drafts:** `docs/prompts.md`. **Runner:** `spikes/s4_questions.py --jev --llm`, blocked until `JEV_API_KEY` and `MISTRAL_API_KEY` are set.
- **Jev API** (exactly as documented):
- **Confusion matrix:** Jev vs LLM vs Jev + EDS vs both together, for the 7 kinds of statement, accept/refuse, Q4 (doctor / someone else / nobody) and Q6:
- **Unsafe ✅:** must be 0 · **🟠 rate:**
- **`tau_conf` q1..q6 and routing:**
- **Question wording that worked** (design notes, not code):

## S5: naive scribe
- **Prompt draft:** `docs/prompts.md`. **Runner:** `spikes/s5_scribe.py`, blocked until `MISTRAL_API_KEY` is set (it uses `SCRIBE_MODEL`, default `mistral-large-latest`).
- **LLM:**
- **Errors on the §7.10 script over 10 runs:** ibuprofen written as a prescription __/10 · sick note 3 days __/10 · blood test written as done __/10
- **Prompt adjustment, if any (C1):**
- **Stability over 5 runs** (identity matched via the log vs via the note):
- **C7 / B19:**

## S6: TV tag (optional)
- **Scores on TV vs live speech; threshold; keep it:**

## S8: normalizer and drug reference
**Done 2026-10-06.**
- **Phrase set (kept):** `fixtures/normalizer_phrases.json`. 30 phrases with the expected values; session date Saturday 2026-10-10.
- **Library results** (`spikes/s8_libraries.py`, Python 3.12):
  - **text2num** (`alpha2digit(text, "fr", threshold=0)`): **keep, for number words only.**
    - Right: mille → 1000, cinq cents → 500, quatre → 4, trois fois → 3 fois, deux semaines → 2 semaines, quinze jours → 15 jours.
    - Quirks:
      - "un demi" comes out as "1 demi", so handle *demi* **before** calling it;
      - "zéro virgule cinq" comes out as "0,5", so parse comma decimals.
    - It doesn't handle units, frequencies or dates.
  - **dateparser 1.4.3: reject.**
    - It returns *dates* for durations ("deux semaines" → 2026-10-24), which is misleading.
    - It returns None for "jusqu'à vendredi", "lundi" and "jusqu'au 15".
  - **EDS-NLP 0.23 dates: partial, not used for dates.**
    - Right: hier → −1 day (useful as the 24 h window for reported intake), "dans trois jours" → +3 days, "pendant cinq jours" → 5-day duration.
    - Misses: weekdays, "jusqu'au 15", "deux semaines" on its own.
    - Keep EDS-NLP only for its qualifiers in Tier 2.
- **What our own code must cover** (Task 2):
  - units: g / mg / gramme(s) / milligramme(s), with comma decimals;
  - "demi";
  - frequencies: "N fois par jour", "matin/midi/soir", "toutes les N heures";
  - counts × strength: "quatre, des 400", "5 Doliprane 1000";
  - durations: "N jours/semaines/mois", "quinze jours", "pendant N jours";
  - relative dates: "jusqu'à <weekday>", "<weekday>", "dans N jours", "jusqu'au N";
  - intake windows: "hier", "aujourd'hui", "par jour".
- **BDPM files:** `reference/bdpm/CIS_bdpm.txt` and `CIS_COMPO_bdpm.txt`, downloaded 2026-10-06. **The encoding is ISO-8859-1**, tab-separated, with CRLF line endings in the compositions file.
- **How we got the RCP sections:** `https://base-donnees-publique.medicaments.gouv.fr/affichageDoc.php?specid=<CIS>&typedoc=R`, then strip the HTML and take the text from the **last** "4.2. Posologie et mode d'administration" to the next "4.3. Contre-indications". The first occurrence is the table of contents. Cached as `reference/rcp/<substance>_<CIS>_4.2.txt` alongside the raw HTML.
- **`reference/drug_limits.json`** (adults; each number checked against its quote and against the cached section by `spikes/s8_verify_limits.py`; a deliberately wrong value is correctly rejected):

  | Substance | Product (CIS) | Usual/24 h (no medical advice) | Max/24 h | Max per dose | Min interval | Number in quote ✓ | Read ✓ |
  |---|---|---|---|---|---|---|---|
  | paracetamol | DOLIPRANE 1000 mg (60234100) | 3000 mg | 4000 mg (medical advice only) | 1000 mg | 4 h | ✓ | ✓ (Claude, 2026-10-06; to be re-read by a teammate) |
  | ibuprofene | ADVIL 400 mg (63646874) | — | 1200 mg | 400 mg | 6 h | ✓ | ✓ (same) |
  | tramadol | TRAMADOL ALMUS 50 mg (67105161) | — | 400 mg | 100 mg | 4 h | ✓ | ✓ (same) |

- **N in line 4 = 4.** 4 × 400 mg = 1600 mg in 24 h, above the RCP maximum of 1200 mg/day, so `dose_alert` fires. The script stays « Hier j'en ai pris quatre, des 400 ».
- **Paracetamol in line 6:** "trois fois mille milligrammes" = 3000 mg/day, which equals the 3000 mg/day maximum without medical advice. The demo info note « conforme à la posologie usuelle (3 g/jour, RCP) » is confirmed by the real RCP.

## Values to paste in (end of the week)
```json
{
  "tau_D_solo": null, "tau_notD": null, "tau_D": null, "tau_P": null, "m": null,
  "tau_same": null, "tau_cons": null, "min_seconds": 1.0, "learn_seconds": null,
  "reply_window_s": 2.0, "max_patient_templates": 5,
  "tau_conf": {"q1": null, "q2": null, "q3": null, "q4": null, "q5": null, "q6": null},
  "pause_s": 1.2, "max_interval_s": 5.0,
  "silence_ms": 600, "min_speech_ms": 250, "max_sentence_s": 15
}
```
