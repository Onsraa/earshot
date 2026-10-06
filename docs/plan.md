# Earshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Earshot hackathon demo.
- **Input:** live French consultation audio.
- **Voices:** the doctor's voice was recorded once in advance; the patient's voice is learned automatically.
- **Labels:** each sentence is tagged DOCTOR or PATIENT from the voice.
- **Note:** a naive scribe writes the consultation note.
- **Verdicts:** each action gets ✅ authorized, 🟠 to confirm, or 🔴 blocked, with reasons. Doses are checked against official drug information.
- **Delivery:** shown on a projected screen; it can also be replayed offline.

**Architecture:**
- **One process.** A single Python process on one asyncio event loop.
- **Audio → sentences.** Audio goes through: capture → sentence cutting → transcription + voice check. The voice check includes candidate voices and choosing which one is the patient. The result is a stream of `Sentence`s.
- **Sentences → action log.** Narrow, per-sentence model questions add entries to an append-only action log.
- **Note → verdicts.** A naive LLM scribe writes the note. Code then gives verdicts by checking the note against the log, the rules and the drug reference.
- **Display.** Versioned snapshots go over a WebSocket to a single HTML/JS page.
- **Build order:** tiers. Tier 1 must run end to end first.

**Tech Stack:**
- **Server and audio:** Python 3.11+, FastAPI + uvicorn (WebSockets), numpy, soundfile, sounddevice, silero-vad, torch + speechbrain (ECAPA).
- **AI services:** mistralai (Voxtral + LLM), or Bedrock for the LLM. The Jev client follows the API recorded in S4.
- **Text:** text2num.
- **Tests:** pytest + pytest-asyncio + httpx.
- **Tier 2:** pyannote.audio, edsnlp. **Tier 3:** YAMNet.
- **Front end:** plain HTML/JS/CSS.

**Companion docs** (written in Phase 0; read them before Task 1):
- `docs/architecture.md`: components, concurrency, state machines, REST/WebSocket interface, snapshot format, config, timing, degradation.
- `docs/models.md`: every model, its verified version and API, and its fallbacks.
- `docs/prompts.md`: prompt spec v1, including the single batched Jev call per sentence.
- `docs/infra.md`: environment, pinned dependencies, keys, downloads, hardware, runbook.
- `docs/test-results.md`: the Phase 0 values (thresholds, limits, APIs).

**Spec:** `earshot/docs/spec.md` (v3). Before starting any task, read:
- §2.1 Tiers
- §2.2 Operating domain
- §5.1 Data formats
- §6 Components
- §7 Rules
- §7.10 The demo scenario

## Global Constraints
- **When code is written:** all product code is written during the event (10–11 October, 36 h). Phase 0 code is throwaway. Only these are kept:
  - recordings
  - `reference/drug_limits.json` with its quotes
  - the cached RCP texts (RCP = the drug's official summary of product characteristics)
  - `docs/test-results.md`
- **Stack:** **Python 3.12** (verified; 3.14 not tested with these libraries); FastAPI + WebSockets; one HTML/JS page with no framework; runs on one Mac.
- **Pinned dependencies** (`docs/infra.md` §1, verified together on 2026-10-06): fastapi 0.142.2, uvicorn 0.54.0, httpx 0.28.1, numpy 2.5.3, soundfile 0.14.0, sounddevice 0.5.6, torch 2.14.1, torchaudio 2.11.0, speechbrain 1.1.1, silero-vad 6.2.3, mistralai 3.0.0, text2num 3.1.0. Tier 2 adds pyannote.audio 4.0.7 and edsnlp 0.23.0. Tests use pytest 9.1.1 and pytest-asyncio 1.4.0.
- **API facts verified in Phase 0** (`docs/models.md`):
  - **Mistral:** `from mistralai.client import Mistral` (SDK 3.0.0). Voxtral calls use `model="voxtral-mini-latest"` with `timestamp_granularities=["word"]` and **no** `language` (the two are mutually exclusive), then check `response.language == "fr"`.
  - **Jev:** `POST https://api.typesafe.ai/v1/systemone`, body `{state, model:"jev-latest", questions}`, header `Authorization: Bearer`.
  - **BDPM:** files are ISO-8859-1, tab-separated.
- **Language:** screen text in French. Code, identifiers and comments in English.
- **Who spoke comes only from the voice check** (`audio/voice.py`), never from the text or from a model. Speaker turn-taking may only be used to decide *patient vs other*, never *doctor* (spec §6.4).
- **Models answer questions; code decides authority.** A detail counts only if the normalizer finds it in the target sentence's own words. Dose comparisons use standard quantities in code, never semantic similarity (spec §6.6–6.8).
- **Every external call goes through `Cache.call`.**
- **Tier order:** no Tier 2 task before Task 16 passes. Tier 3 only once Tiers 1–2 are stable. **Code freeze at hour 32.**
- **Configuration:** thresholds come only from `config/thresholds.json`; model choices from `config/models.json`; dose limits from `reference/drug_limits.json`. No hard-coded values.
- **Privacy:**
  - the doctor's voiceprint is stored in `~/.earshot/doctor.npz`;
  - the patient's voiceprint and the candidate voices stay in memory only and are cleared on reset;
  - no real patient data.
- **Time limits:**
  - a sentence is labelled within 2 s for 9 out of 10 sentences;
  - the patient's voice is learned by the end of their first answer;
  - a spoken confirmation shows within 5 s;
  - the final check takes at most 10 s.
- **Reasons** (`REASONS` in `brain/rules.py`, exact text):

  | Key | Text |
  |---|---|
  | `no_doctor` | `aucune phrase du médecin` |
  | `uncertain_voice` | `voix incertaine` |
  | `withdrawn` | `retiré par le médecin` |
  | `alternatives` | `alternative proposée, pas choisie` |
  | `conditional` | `ordonnance conditionnelle` |
  | `refused` | `proposition refusée` |
  | `not_accepted` | `proposition non acceptée` |
  | `contradicts` | `détail contredit le médecin (médecin : {x})` |
  | `patient_detail` | `détail dit par le patient` |
  | `third_party_detail` | `détail issu d'un conseil d'un tiers` |
  | `unspoken_detail` | `détail non prononcé` |
  | `status_differs` | `statut différent` |
  | `low_confidence` | `confiance faible` |
  | `veto` | `négation/hypothèse détectée` |
  | `patient_diagnosis` | `diagnostic issu du patient` |
  | `third_party` | `conseil d'un tiers rapporté par le patient` |
  | `above_max` | `dose au-dessus du maximum (RCP : {x})` |
  | `unknown_drug` | `hors cadre : médicament inconnu` |
  | `pediatric` | `hors cadre : posologie pédiatrique` |
  | `unparsed` | `hors cadre : action non reconnue` |
  | `unknown_voice` | `hors cadre : voix inconnue` |
  | `not_patient` | `voix non retenue comme patient` |
  | `ambiguous` | `action ambiguë` |
  | `missing` | `manquant dans la note` |
  | `confirmed` | `confirmé par le médecin` |

- **Info notes** (`INFO`, exact text):

  | Key | Text |
  |---|---|
  | `usual` | `conforme à la posologie usuelle ({x}, RCP)` |
  | `within` | `dans les limites (max {x}, RCP)` |
  | `no_reference` | `référence indisponible` |
  | `reported` | `rapporté par le patient` |

- **Alert texts:**
  - `Prise rapportée : {substance} {mg} mg en 24 h — au-dessus du maximum (RCP : {x})`
  - `Fausse attribution : "{sentence}" — aucune phrase du médecin ne correspond`
  - `hors cadre : médecin non enregistré`
  - `hors cadre : médecin non reconnu`

## Review Focus
1. **The stage audio doesn't match the enrollment recording** (lower volume, noise, distance). Expected: labels fall back to UNCERTAIN and never go PATIENT→DOCTOR. Test: `test_noisy_patient_never_doctor` in Task 13.
2. **A service fails or times out mid-consultation.** Expected:
   - the status light turns red and a `service_down` alert appears;
   - affected verdicts stay `pending`;
   - sentences keep getting labelled.

   Test: `test_service_failure_keeps_labelling` in Task 14.
3. **The scribe returns invalid JSON, or an action that can't be parsed.** Expected: no crash. Invalid JSON keeps the previous note; an unparsed action gets 🟠 `hors cadre : action non reconnue`. Tests: Task 7 and Task 10.
4. **Drug names and doses spelled many ways.** Mixed case, missing accents or brand names; "1g", "1 g", "1000mg", "mille milligrammes". Expected: the same key and the same standard quantity. Tests: `test_drug_variants_same_key` (Task 3) and `test_dose_spellings` (Task 2).
5. **A second consultation starts after the first.** Expected:
   - sentences, log, note, verdicts, candidates and the patient's voiceprint are all cleared;
   - **the doctor's voiceprint stays loaded**;
   - the patient's voice is learned again.

   Test: `test_reset_keeps_doctor_only` in Task 14.

---

## File structure (created at the event)
```
earshot/
  pyproject.toml
  config/thresholds.json        # from test-results.md
  config/models.json
  reference/drug_limits.json    # from S8: DrugLimits per substance, with quote and source_url
  reference/bdpm/               # BDPM files (brand → substance, strengths)
  reference/rcp/                # cached RCP posology sections (Tier 2 live retrieval)
  fixtures/demo_scenario.json   # spec §7.10 as data
  fixtures/drug_limits_test.json# small fixed limits used by unit tests
  fixtures/audio/               # Phase 0 recordings + labels
  fixtures/cache/               # offline answers recorded during rehearsal
  src/earshot/
    models.py
    brain/normalize.py          # numbers, units, frequencies, durations, dates → DoseQuantity
    brain/drugs.py              # synonyms, BDPM, strengths, keys, term finder
    brain/reference.py          # DrugLimits loader + dose checks (+ Tier 2 live retrieval)
    brain/log.py                # ActionLog + derived state filtered by current labels
    brain/rules.py              # REASONS, INFO, action_verdict, line_verdict
    brain/matcher.py            # scribe output → verdicts, omissions, alerts
    brain/questions.py          # Q1–Q6, spotlighting, process_sentence
    brain/scribe.py             # naive scribe prompt, neutral transcript, scheduler
    brain/second_check.py       # Tier 2: EDS-NLP veto
    audio/capture.py            # mic / WAV → chunks
    audio/cutter.py             # Silero VAD sentence cutter
    audio/transcribe.py         # Voxtral / Whisper
    audio/voice.py              # doctor enrollment, phases A/B, candidates, commit
    audio/segment.py            # Tier 2: segmentation-3.0
    audio/media_tag.py          # Tier 3: YAMNet
    infra/cache.py
    infra/clients.py            # ModelClient, Jev/LLM adapters, routing
    infra/trail.py              # Tier 2: audit trail
    pipeline.py                 # Session: state, ordering, relabel, snapshots, final check, reset
    server.py
    web/index.html, web/app.js, web/style.css
  tests/
```

---

## Phase 0 — this week (throwaway; spec §12)
**Status on 2026-10-06** (branch `earshot-phase0`; details in `docs/test-results.md`):
- **S8:** ✅ done. `reference/drug_limits.json` holds the real RCP limits with checked quotes; N = 4 is confirmed; the normalizer study is written up.
- **S7:** email drafted in `docs/organizer-email.md`; **you need to send it**.
- **S1a:** tooling and guide ready, and a synthetic dry run passed (8/8, 9/9). **Waiting on the actors' recording session.**
- **S3, S4, S5:** runners, the 128-sentence S4 set and the prompts are ready. **Waiting on API keys.**
- **S2, S6, S1b:** waiting on the S1a recordings.

Code goes in `earshot/spikes/` and is **deleted at the end of the week**. Recordings go in `fixtures/audio/` as `*.wav`, each with a `*.labels.json` of `[{start, end, speaker, text}]`. Results go in `docs/test-results.md`.

- [ ] **S7 (day 1):** email the organizers. Ask:
  - whether code written before the event is allowed;
  - whether actors must use stage microphones;
  - what the wifi is like;
  - how long the demo slot is.
- [ ] **S1a (Dev A, 2.5 h, first):**
  1. Record the doctor's voice once: 2–3 readings of 20–30 s, at the demo spot, with the demo Mac and microphone.
  2. Record the §7.10 script 5 times, 3 minutes of free conversation, and **1 take with a TV clip played before line 2**. Label everything.
  3. In `spikes/s1a.py`, run phases A/B, the candidate voices and the commit rule (spec §6.4) with ECAPA and WeSpeaker. Try learning the patient's voice from 4, 6 and 8 s of speech. Search τ_D_solo, τ_notD, τ_D, τ_P, m and τ_same.
  4. Pass criteria:
     - 100% correct on the script;
     - 0 patient segments labelled DOCTOR;
     - 0 doctor segments in a candidate voice;
     - the commit picks the patient in the TV take;
     - ≤10% UNCERTAIN in free conversation.

     Record the model, the thresholds and the learning duration.
- [ ] **S2 (Dev A, 1 h):** measure end of sentence → label + text, 90th percentile, on CPU and on MPS (Apple GPU).
- [ ] **S3 (Dev A, 1.5 h):** run Voxtral on 20 French sentences, with and without drug-name hints. Record the endpoint, model, whether word timestamps are returned, and cost. Decide between Voxtral and Whisper.
- [ ] **S4 (Dev B, 3 h):**
  1. Read the Jev docs and record its exact API.
  2. Write ≥10 French sentences for each kind of statement, plus accept/refuse, Q4 (doctor / someone else / nobody) and Q6 (reported intake). Cover spec B3, B4, B7, B8, B11, B24, B29, T2, T3 and T4, plus the adversarial set.
  3. Compare Jev, the LLM, Jev + EDS-NLP, and both together.
  4. Choose a τ_conf per question so that **no unsafe ✅** occurs. Record the question wording that worked.
- [ ] **S5 (Dev B, 1.5 h):**
  1. Write the naive scribe prompt (spec §6.5).
  2. Run it 10 times on the §7.10 script and record its errors: ibuprofen written as a prescription, a 3-day sick note, the blood test written as done.
  3. Run it 5 times on the same partial transcript and record how much action identities change between runs.
  4. Check C7 and B19.
  5. If the scribe makes no error, adjust **only the scribe prompt** so it behaves like real products (spec C1), and record that.
- [ ] **S8 (Dev B, 2.5 h):**
  1. Run ~30 normalizer phrases through text2num, EDS-NLP and dateparser.
  2. Download the BDPM into `reference/bdpm/`.
  3. Find out how to get the RCP posology section (section 4.2) for paracetamol, ibuprofen and tramadol (plus synonyms), and cache them in `reference/rcp/`.
  4. Have an LLM extract `DrugLimits` with quotes into `reference/drug_limits.json`, then check that every number appears in its quote, and read them through.
  5. Set N in line 4 so that N × 400 mg is above the ibuprofen maximum.
- [ ] **S1b (Dev A, 4 h, after S1a passes):** record the hard-conditions set and a set of other voices; compare variants A–E; record per-duration thresholds and the replay/clone results.
- [ ] **S6 (Dev A, 1 h, optional):** YAMNet "Television/Radio" on TV vs live speech.
- [ ] **End of week:**
  - `git rm -r spikes/`;
  - commit `docs/test-results.md`, `fixtures/audio/`, `reference/`;
  - copy the chosen values into the ready-to-paste JSON block in `test-results.md`.

---

## Tier 1 — must work cleanly (hours 0–18)

### Task 1: Skeleton, data types, fixtures (both, hours 0–2)

**Files:**
- Create:
  - `pyproject.toml`
  - `config/thresholds.json`, `config/models.json`
  - `src/earshot/__init__.py`, `src/earshot/models.py`
  - `fixtures/demo_scenario.json`, `fixtures/drug_limits_test.json`
- Test: `tests/test_models.py`

**Interfaces:**
- **Produces in `models.py`** (spec §5.1, field names verbatim):
  - `Word`
  - `Sentence(id, start, end, text, words, speaker, scores, media_tag=None, final_label=True)`
  - `ActionEvent`
  - `Mention(sentence_id, speaker, key, details, source)`
  - `Claim(sentence_id, key, details, attributed_to)`
  - `DoseQuantity(substance, per_intake_mg=None, intakes_per_day=None, daily_mg=None, min_interval_h=None, duration_days=None)`
  - `DrugLimits(substance, population, usual_daily_mg=None, max_daily_mg=None, max_per_intake_mg=None, min_interval_h=None, quote="", source_url="")`
  - `IntakeReport(sentence_id, substance, daily_mg, window_h=24)`
  - `ScribeAction`
  - `NoteLine`
  - `Verdict(target, status, reasons, info, evidence_ids, provisional=True)`
  - `Alert`
  - `VoiceState(doctor_loaded, patient, patient_seconds, candidates)`
  - `to_json(obj) -> dict`
  - `Literal` aliases, with values verbatim from spec §5.1.
- **`config/thresholds.json`** keys:
  - voice: `tau_D_solo`, `tau_notD`, `tau_D`, `tau_P`, `m`, `tau_same`, `tau_cons`, `min_seconds` (1.0), `learn_seconds` (from S1a), `reply_window_s` (2.0), `max_patient_templates` (5)
  - questions: `tau_conf` {q1..q6}
  - scribe: `pause_s` (1.2), `max_interval_s` (5.0)
  - sentence cutter: `silence_ms` (600), `min_speech_ms` (250), `max_sentence_s` (15)
- **`fixtures/demo_scenario.json`:**
  - `{"session_date": "2026-10-10", "n_line4": 4, "sentences": [...], "scribe_outputs": {"after_4": {...}, "after_8": {...}}, "expected": {"after_4": {...}, "after_8": {...}}}`
  - Spec §7.10, lines 1–8.
  - **`expected.after_8.verdicts`:**
    - `prescription:ibuprofene` → blocked [`retiré par le médecin`, `conseil d'un tiers rapporté par le patient`]
    - `prescription:paracetamol` → authorized, info [`conforme à la posologie usuelle (3 g/jour, RCP)`]
    - `sick_leave` → blocked [`détail contredit le médecin (médecin : 14 jours)`]
    - `test_order:prise de sang` → to_confirm [`ordonnance conditionnelle`]
  - **Alerts:** exactly one `dose_alert` (ibuprofen) and no `false_attribution`.
  - **`expected.after_4.verdicts`:**
    - `prescription:ibuprofene` → blocked [`aucune phrase du médecin`, `conseil d'un tiers rapporté par le patient`]
    - `sick_leave` → blocked [`aucune phrase du médecin`, `conseil d'un tiers rapporté par le patient`]
- **`fixtures/drug_limits_test.json`** (test-only values):
  - paracetamol: usual 3000, max 4000, min interval 4 h, quote "…3 g par jour…4 g…"
  - ibuprofen: max 1200, quote "…1200 mg…"

- [ ] **Step 1: Write the tests.**
  - `test_sentence_roundtrip`
  - `test_fixture_loads`: every sentence builds; `expected.after_8.verdicts["sick_leave"]["status"] == "blocked"`.
- [ ] **Step 2:** `cd earshot && pytest tests/test_models.py -v` → FAIL.
- [ ] **Step 3:** write the files listed above.
  - `pyproject.toml`: use the pinned block in `docs/infra.md` §1.
  - `config/models.json`: as in `docs/architecture.md` §6.
  - Config values: from the ready-to-paste JSON in `docs/test-results.md`.
  - `reference/` already exists from Phase 0: `drug_limits.json`, `bdpm/`, `rcp/`, `drug_hints.txt`.
- [ ] **Step 4:** run the tests → PASS.
- [ ] **Step 5:** `git add -A && git commit -m "feat: skeleton, data types, demo fixtures"`

### Task 2: Normalizer and standard dose quantities (Dev B)

**Files:**
- Create: `src/earshot/brain/normalize.py`
- Test: `tests/test_normalize.py`

**Interfaces:**
- Consumes: `DoseQuantity` (Task 1).
- Produces:
  - `normalize_text(text) -> str`: handles "demi" first, then converts number words with text2num `alpha2digit` (check the API at the event).
  - `parse_dose_mg(text) -> float | None`
  - `parse_frequency(text) -> tuple[int | None, tuple[str, ...]]`
  - `parse_duration(text, session_date) -> dict`
  - `parse_count(text) -> int | None`
  - `dose_quantity(text: str, substance: str, strengths_mg: list[float], session_date: date) -> DoseQuantity`
    - `daily_mg` = `per_intake_mg × intakes_per_day`, or a total stated directly ("3 g par jour").
    - A count with a strength in the text ("quatre, des 400") gives count × strength. The strength must be one of `strengths_mg`, or stated in mg.
    - A count with no strength, when `len(strengths_mg) != 1`, leaves `per_intake_mg` as None.
  - `extract_details(text, session_date, substance=None, strengths_mg=()) -> dict`: flat details (`dose_mg`, `per_day`, `daily_mg`, `duration_days`, `duration_months`, `status`), taken from the text itself.
  - `details_in_text(details, text, session_date) -> dict`
  - `format_detail(field, value) -> str`:
    - `duration_days` → `"{v} jours"`
    - `daily_mg` → `"{v/1000:g} g/jour"` when ≥ 1000, otherwise `"{v:g} mg/jour"`
    - `dose_mg` → `"{v:g} mg"`
    - `per_day` → `"{v} fois/jour"`

- [ ] **Step 1: Write the tests.** `D = date(2026,10,10)`.
  - `test_dose_spellings`: "1 g", "1g", "un gramme", "1000mg", "mille milligrammes" → 1000; "zéro virgule cinq milligramme" → 0.5.
  - `test_frequency`:
    - "trois fois par jour" → 3
    - "matin, midi et soir" → (3, MORN/NOON/EVE)
    - "toutes les 8 heures" → 3
    - "toutes les 6 heures" → 4
    - "matin et soir" → 2
  - `test_duration`:
    - "deux semaines" → 14
    - "une semaine" → 7
    - "quinze jours" → 15
    - "un mois" → months 1
  - `test_relative_dates`:
    - "jusqu'à vendredi" → 6
    - "lundi" → 2
    - "dans trois jours" → 3
    - "jusqu'au 15" → 5
  - `test_same_daily_dose` (spec D1/D2): `dose_quantity(x, "paracetamol", [500, 1000], D).daily_mg == 3000` for each x in:
    - "trois fois mille milligrammes par jour"
    - "1 g trois fois par jour"
    - "1000 mg matin, midi et soir"
    - "1000 mg toutes les 8 heures"
    - "3 g par jour"
  - `test_count_times_strength` (D3):
    - "hier j'en ai pris quatre, des 400" with ibuprofen [200, 400] → daily 1600
    - "5 Doliprane 1000" with paracetamol [500, 1000] → daily 5000
  - `test_count_without_strength_ambiguous` (D4): "un comprimé" with [500, 1000] → `per_intake_mg is None`.
  - `test_details_in_text_rejects_context_values`.
- [ ] **Step 2:** run the tests → FAIL.
- [ ] **Step 3:** implement. Use regex on the normalized text and `datetime` for dates.
- [ ] **Step 4:** run the tests → PASS.
- [ ] **Step 5:** `git commit -am "feat: normalizer and standard dose quantities"`

### Task 3: Drug names, strengths, keys (Dev B)

**Files:**
- Create: `src/earshot/brain/drugs.py`
- Test: `tests/test_drugs.py`

**Interfaces:**
- Produces:
  - `SYNONYMS` (minimum set, folded):

    | Brand or variant | Substance |
    |---|---|
    | doliprane, dafalgan, efferalgan | paracetamol |
    | advil, nurofen | ibuprofene |
    | clamoxyl | amoxicilline |
    | kardegic | aspirine |
    | tramadol | tramadol |

  - `fold(name) -> str`
  - `load_bdpm(directory) -> Bdpm`, where `Bdpm` has `brand_to_substance: dict[str, str]` and `strengths_mg: dict[str, list[float]]`. Join the two files on the CIS code. Their layout was verified in Phase 0:
    - **both files:** `encoding="iso-8859-1"`, tab-separated;
    - **`CIS_bdpm.txt`:** column 1 is the CIS code, column 2 the name (e.g. "DOLIPRANE 1000 mg, comprimé");
    - **`CIS_COMPO_bdpm.txt`:** column 1 CIS, 4 substance name, 5 dosage with a decimal comma ("1,00 mg"), 7 nature (`SA` = active substance; keep only `SA` rows). This file has CRLF line endings.
  - `generic_name(name, bdpm=None) -> str`
  - `strengths(substance, bdpm=None) -> list[float]`
  - `make_key(type, target, bdpm=None) -> str`: `"sick_leave"`, or `f"{type}:{generic_name or fold(target)}"`.
  - `find_drug_terms(text, bdpm=None) -> list[str]`
- [ ] **Step 1: Write the tests.**
  - `test_drug_variants_same_key`: "Doliprane", "DOLIPRANE", "paracétamol", "Paracetamol 1000 mg", "Dafalgan" → `prescription:paracetamol`.
  - `make_key("sick_leave", None) == "sick_leave"`.
  - `find_drug_terms("de l'ibuprofène… du Doliprane") == ["ibuprofene", "paracetamol"]`.
  - `test_load_bdpm_strengths` on a 4-line sample in `tmp_path` → `strengths("ibuprofene") == [200, 400]`.
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS).
- [ ] **Step 5:** `git commit -am "feat: drug names, strengths, keys"`

### Task 4: Drug reference and dose checks (Dev B)

**Files:**
- Create: `src/earshot/brain/reference.py`
- Test: `tests/test_reference.py`

**Interfaces:**
- Consumes: `DrugLimits`, `DoseQuantity`, `IntakeReport`, `Alert` (Task 1); `format_detail`, `normalize_text` (Task 2).
- Produces:
  - `load_limits(path) -> dict[str, DrugLimits]`. It **drops any limit whose number does not appear in `normalize_text(quote)`** (spec D8) and logs a warning.
    - It skips keys starting with `_` (e.g. `_note`).
    - `usual_daily_mg` means the "maximum without medical advice" (paracetamol 3000); `max_daily_mg` means the absolute maximum (paracetamol 4000, with medical advice). Spec D9.
  - `limits(substance, table) -> DrugLimits | None`
  - `check_prescription(dq: DoseQuantity, table) -> tuple[str | None, str | None]`, returning `(reason_key_or_None, info_text_or_None)`:
    - substance not in the table → `("unknown_drug", None)`
    - `daily_mg > max_daily_mg`, or interval shorter than `min_interval_h` → `("above_max", None)`, with x = the formatted maximum
    - `daily_mg ≤ usual_daily_mg` → `(None, INFO.usual)` with the formatted usual daily dose
    - `daily_mg ≤ max_daily_mg` → `(None, INFO.within)`
    - missing limits → `(None, INFO.no_reference)`
  - `check_intake(report: IntakeReport, table) -> Alert | None`: a `dose_alert` with the exact text from the Global Constraints when `daily_mg > max_daily_mg`.
- [ ] **Step 1: Write the tests** (using `fixtures/drug_limits_test.json`):
  - `test_rejects_number_not_in_quote`
  - `test_paracetamol_3g_is_usual` → info `conforme à la posologie usuelle (3 g/jour, RCP)`
  - `test_paracetamol_5g_above_max` → `above_max`
  - `test_unknown_drug`
  - `test_intake_alert_ibuprofen_1600` → the alert text contains `1600 mg en 24 h`
  - `test_intake_below_max_no_alert`
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS).
- [ ] **Step 5:** `git commit -am "feat: drug reference and dose checks"`

### Task 5: Action log with derived state (Dev B)

**Files:**
- Create: `src/earshot/brain/log.py`
- Test: `tests/test_log.py`

**Interfaces:**
- Consumes: Task 1 types.
- Produces:
  - **`class ActionLog`**, append-only:
    - `append_event(...) -> ActionEvent`
    - `add_mention(m)`, `add_claim(c)`, `add_intake(r)`
    - `events(key=None)`, `keys()`, `clear()`
    - `open_offer(sentence_id, within=3) -> ActionEvent | None`
  - **`class View(log, label_of: Callable[[int], Speaker])`**: the derived state, always recomputed from the **current** labels.
    - `mentions(key)`, `claims()` and `intakes()` exclude sentences whose current label is `OTHER`.
    - `key_state(key) -> KeyState`.
  - **`KeyState(decisive, answer, doctor_details, patient_details, third_party_details, uncertain_only)`**:
    - `doctor_details` holds the latest value per field from DOCTOR decision/offer events.
    - `patient_details` comes from `source="self"` mentions.
    - `third_party_details` comes from `source="third_party"` mentions.
- [ ] **Step 1: Write the tests.**
  - `test_append_only_seq`
  - `test_latest_decisive_wins`
  - `test_offer_answer`
  - `test_open_offer_window`
  - `test_latest_detail_wins`
  - `test_uncertain_only`
  - `test_relabel_drops_mentions`: a mention from sentence 2; then `label_of(2)` returns OTHER → `mentions(key) == []`, and `events()` is unchanged.
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS).
- [ ] **Step 5:** `git commit -am "feat: append-only action log with label-aware view"`

### Task 6: Authority rules (Dev B)

**Files:**
- Create: `src/earshot/brain/rules.py`
- Test: `tests/test_rules.py`

**Interfaces:**
- Consumes: `View`/`KeyState` (Task 5), `check_prescription` (Task 4), `format_detail` (Task 2).
- Produces:
  - `REASONS` and `INFO`, exactly as in the Global Constraints.
  - `action_verdict(action: ScribeAction, view: View, table, tau_conf: float) -> Verdict`: spec §7.4, steps 1–6.
    - Use the §7.3 details rule, comparing standard values.
    - `tau_conf` is `thresholds.tau_conf["q2"]`.
    - The worst status wins, and every reason that applies is listed.
    - Prescriptions and renewals go through `check_prescription` using the action's `DoseQuantity`.
  - `line_verdict(line: NoteLine, support: list[Sentence], third_party_ids: set[int]) -> Verdict`: spec §7.1.
    - A history line supported only by third-party sentences → authorized, with info `rapporté par le patient`.
- [ ] **Step 1: Write the tests.** One per case; each checks `status` and `reasons`/`info`.
  - Spec cases: B1, B2, B5/B6, B9, B10, B15, B17, B22, B24, B25, B28, B30.
  - `test_contradiction_14_days` → blocked `détail contredit le médecin (médecin : 14 jours)`
  - `test_third_party_reason` (T1): no doctor event, a third-party mention → blocked [`aucune phrase du médecin`, `conseil d'un tiers rapporté par le patient`]
  - `test_withdrawn_plus_third_party` (the ibuprofen case)
  - `test_above_max_to_confirm` (D6)
  - `test_unknown_drug_hors_cadre` (H3)
  - `test_usual_info` (D9)
  - `test_veto`
  - `test_uncertain_only`
  - The line cases.
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS).
- [ ] **Step 5:** `git commit -am "feat: authority rules with dose checks and third-party advice"`

### Task 7: Note matcher (Dev B)

**Files:**
- Create: `src/earshot/brain/matcher.py`
- Test: `tests/test_matcher.py`

**Interfaces:**
- Consumes: Tasks 2–6.
- Produces:
  - `parse_scribe_output(raw, session_date, bdpm=None) -> tuple[list[NoteLine], list[ScribeAction], list[str]]`. Unknown types go to the third list. It never raises.
  - `match(lines, actions, unparsed, view, sentences, line_support, table, tau_conf) -> tuple[list[Verdict], list[Alert]]`:
    - duplicate keys → `action ambiguë` plus an `ambiguous_action` alert;
    - unparsed → to_confirm `hors cadre : action non reconnue`;
    - adds omissions, false attributions and the intake `dose_alert`s from `check_intake`.
  - `omissions(actions, view) -> list[Verdict]`
  - `false_attributions(view) -> list[Alert]`: only claims with `attributed_to == "doctor"`.
- [ ] **Step 1: Write the tests.**
  - `test_demo_after_4` and `test_demo_after_8`: statuses, reasons, info and alerts equal the fixture's `expected`.
  - `test_duplicate_key_ambiguous` (C10)
  - `test_omission` (B27)
  - `test_unparseable_action_to_confirm`
  - `test_third_party_claim_is_not_false_attribution` (T2)
  - `test_doctor_claim_without_match_is_false_attribution` (T3)
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS).
- [ ] **Step 5:** `git commit -am "feat: note matcher, omissions, alerts"`

### Task 8: Cache and model clients (Dev B)

**Files:**
- Create: `src/earshot/infra/cache.py`, `src/earshot/infra/clients.py`
- Test: `tests/test_cache.py`, `tests/test_clients.py`

**Interfaces:**
- Produces:
  - `OfflineMiss`, `ServiceDown`
  - `Cache(directory, mode)` with `async call(service, model, payload, fn) -> dict`. The key is the sha256 of `service|model|sorted JSON payload`.
  - `ModelClient` protocol:
    - `async choice(question, prompt, options) -> tuple[str, float]`
    - `async yes_no(question, prompt) -> tuple[bool, float]`
  - `JevClient`: `POST https://api.typesafe.ai/v1/systemone` with `{"state", "model": "jev-latest", "questions": {...}}`.
    - Also exposes `async batch(state: str, questions: dict) -> dict[str, tuple[str|bool, float]]`. **One call per sentence** (`docs/prompts.md` §2).
    - Answer mapping: `noul` → `(p ≥ 0.5, max(p, 1-p))`; `choice` → `(choice, confidence)`.
    - 429 or 529 → one backoff retry, then `ServiceDown`.
  - `LLMClient`: `from mistralai.client import Mistral`; `chat.complete(model, messages, response_format={"type":"json_object"}, temperature=0)`.
    - Also `async json(prompt, schema) -> dict`.
    - Also `batch(...)`, implemented with the fallback prompt in `docs/prompts.md` §3; an answer that isn't one of the options becomes "unknown".
  - `RoutedClient(primary, fallback, tau)`: per question id, keeps the primary's answer when its confidence is ≥ `tau`, otherwise asks the fallback. Adapter timeout: 8 s (Jev, Voxtral), 15 s (LLM).
- [ ] **Step 1: Write the tests.**
  - `test_live_then_offline`
  - `test_offline_miss_raises`
  - `test_key_ignores_dict_order`
  - `test_routing_falls_back_below_tau`
  - `test_routing_keeps_primary_above_tau`
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS).
- [ ] **Step 5:** `git commit -am "feat: cache and model clients"`

### Task 9: Sentence questions Q1–Q6 (Dev B)

**Files:**
- Create: `src/earshot/brain/questions.py`
- Test: `tests/test_questions.py`

**Interfaces:**
- Consumes: Tasks 2–5 and 8.
- Produces:
  - `term_candidates(text, bdpm=None) -> list[tuple[ActionType, str | None]]`. Terms from spec §6.6 Q1, including « reprendre le travail » and « repos » → sick_leave.
  - `spotlight(target, context, nonce) -> str`
  - `KINDS` (7 kinds)
  - **Ruling (Phase 0): Q1 and Q2 are merged.** For each candidate action, a single `choice` question `kind:<key>` has the 7 kinds plus `pas_concerné`. Patient sentences get `about:<key>` (`noul`). Every question for one sentence goes in **one** `client.batch(state, questions)` call, using the exact wording in `docs/prompts.md` §2.
    - *Why:* the input is billed once and it saves round trips.
    - *Cost if wrong:* splitting it back into two calls.
  - `async process_sentence(s, history, log, client, session_date, tau, table, bdpm=None) -> None`:
    - **Q1+Q2 (merged, one batched call):** `kind:<key>` for DOCTOR/UNCERTAIN sentences; `pas_concerné` means not relevant. Patient sentences get `about:<key>`.
    - **Q2 (DOCTOR/UNCERTAIN):** for kinds other than mention/reformulation, appends an event with `details_in_text(extract_details(...))`.
    - **Mentions:** every relevant sentence gets a Mention, with `source` from Q4.
    - **Q4 (PATIENT/UNCERTAIN), `who` in the same batch:** answer is one of `médecin` / `autre personne` / `personne`:
      - "médecin" → a Claim with `attributed_to="doctor"`;
      - "autre personne" → that sentence's mentions get `source="third_party"`.
    - **Q5:** answers to an open offer.
    - **Q6 (PATIENT/UNCERTAIN), `intake` (`noul`) in the same batch:** on reported intake; if yes, an `IntakeReport` with `daily_mg` from `dose_quantity`.
    - **OTHER sentences add nothing.**
  - `async line_support(line, candidates, client) -> list[int]`
- [ ] **Step 1: Write the tests** with a scripted fake client.
  - `test_line4_third_party_and_intake`: scenario line 4 as PATIENT, Q4 → "autre personne", Q6 → yes. Expect:
    - a mention `prescription:ibuprofene`, source third_party;
    - a mention `sick_leave`, source third_party, duration 3;
    - an IntakeReport with ibuprofen daily 1600 (with N=4);
    - no events.
  - `test_line6_three_events`: line 6 as DOCTOR. Expect a withdrawal for ibuprofen, a decision for paracetamol {daily 3000}, and a decision for sick_leave {14}.
  - `test_context_cannot_supply_details` (B22)
  - `test_other_never_adds_anything`
  - `test_q5_accept_closes_offer`
  - `test_spotlight_wraps_context`
  - `test_one_batched_call_per_sentence`: the fake client receives exactly one `batch` call for line 6, containing three `kind:` questions.
  - `test_questions_set_no_unsafe` (marked `@pytest.mark.live`; needs keys): run `fixtures/questions_set.json` through `RoutedClient` → **0 unsafe authorizing answers** (`docs/prompts.md` §8).
- [ ] **Steps 2–4:** run the tests (FAIL), implement with the wording from S4, run the tests (PASS).
- [ ] **Step 5:** `git commit -am "feat: sentence questions Q1–Q6"`

### Task 10: Naive scribe and scheduler (Dev B)

**Files:**
- Create: `src/earshot/brain/scribe.py`
- Test: `tests/test_scribe.py`

**Interfaces:**
- Produces:
  - `SCRIBE_PROMPT`: the version settled in S5.
  - `neutral_transcript(sentences) -> str`: "Locuteur N :", numbered by first appearance. Earshot's labels never appear.
  - `async run_scribe(sentences, client) -> dict | None`
  - `ScribeScheduler(run, pause_s, max_interval_s, clock)` with `latest_run_id`.
- [ ] **Step 1: Write the tests.**
  - `test_neutral_labels_hide_roles`
  - `test_scheduler_pause`
  - `test_scheduler_max_interval`
  - `test_invalid_json_keeps_previous_note`
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS).
- [ ] **Step 5:** `git commit -am "feat: naive scribe and scheduler"`

### Task 11: Capture and sentence cutter (Dev A)

**Files:**
- Create: `src/earshot/audio/capture.py`, `src/earshot/audio/cutter.py`
- Test: `tests/test_cutter.py`

**Interfaces:**
- Produces:
  - `async mic_chunks(device=None, channels=1)`
  - `async wav_chunks(path, realtime=True)`
  - `SpeechSegment(start, end, audio)`
  - `SentenceCutter(silence_ms, min_speech_ms, max_s)` with `feed(chunk) -> list[SpeechSegment]` and `flush()`.
    - Uses silero-vad 6.2.3 `VADIterator(model, threshold=0.5, sampling_rate=16000, min_silence_duration_ms=silence_ms, speech_pad_ms=30)` (signature verified in Phase 0).
    - It returns `{"start": …}` / `{"end": …}` events per 512-sample chunk.
    - Buffer the audio between start and end; enforce `min_speech_ms` and the 15 s cap yourself.
- [ ] **Step 1: Write the tests.**
  - `test_cuts_demo_take`: on `fixtures/audio/s1a_script_take1.wav`, the segment count equals the number of labelled sentences, with boundaries within ±0.3 s.
  - `test_max_length`
  - `test_drops_short_noise`
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS).
- [ ] **Step 5:** `git commit -am "feat: capture and sentence cutter"`

### Task 12: Transcriber (Dev A)

**Files:**
- Create: `src/earshot/audio/transcribe.py`
- Test: `tests/test_transcribe.py`

**Interfaces:**
- Produces:
  - `Transcript(text, words)`
  - `Transcriber` protocol with `async transcribe(audio) -> Transcript`
  - `VoxtralTranscriber(cache, model, drug_hints=None)`:
    - **Call:** `client.audio.transcriptions.complete(model="voxtral-mini-latest", file={"content": wav_bytes, "file_name": "s.wav"}, timestamp_granularities=["word"], context_bias=drug_hints)`, with **no `language`**.
    - **Words:** come from `response.segments[*]` as `{text, start, end}`.
    - **Language:** if `response.language != "fr"`, return the text with a `non_french=True` flag; the pipeline then labels the sentence UNCERTAIN.
    - **Hints:** `drug_hints` comes from `reference/drug_hints.txt`.
    - **Failure:** raises `ServiceDown`.
  - `WhisperTranscriber(model)`
  - `split_words(words, boundaries)`
- [ ] **Step 1: Write the tests.**
  - `test_voxtral_parses_cached_response`
  - `test_split_words`
  - `test_empty_text_is_empty`
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS).
- [ ] **Step 5:** `git commit -am "feat: transcription adapters"`

### Task 13: Voice: doctor enrolled once, patient learned through candidate voices (Dev A)

**Files:**
- Create: `src/earshot/audio/voice.py`
- Test: `tests/test_voice.py`

**Interfaces:**
- Consumes: `config/thresholds.json`, `config/models.json`, Task 1 types.
- Produces:
  - **Embedding:** `Embedder` protocol with `embed(audio) -> np.ndarray` (L2-normalized).
    - `EcapaEmbedder` (or WeSpeaker, per S1a) uses `speechbrain.inference.speaker.EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir=~/.cache/earshot-ecapa)` and `encode_batch(tensor[1, T])`, which gives a `[1, 1, 192]` tensor (verified in Phase 0).
    - Run it with `asyncio.to_thread`.
    - The voice-tracker logic is described in `docs/architecture.md` §4.2. The Phase 0 dry run of that logic (8/8, and 9/9 with the TV speaking first) is the reference behaviour. The code is written again from scratch at the event.
  - **Thresholds:** `Thresholds` dataclass with all the voice keys from Task 1; `load_thresholds(path)`.
  - **Doctor enrollment:**
    - `check_clip_quality(audio, embedder, tau_cons, min_speech_s=15.0) -> tuple[bool, str]`
    - `save_doctor(templates, path)`, `load_doctor(path) -> list[np.ndarray] | None`
  - **`class VoiceTracker(doctor_templates, embedder, th)`**:
    - `label(seg: SpeechSegment, prev_doctor_end: float | None) -> tuple[Speaker, dict, list[tuple[int, Speaker]]]`. It returns this segment's label, its scores, and **relabels**, i.e. earlier sentence ids whose label changed at commit time.
      - **Phase A:** DOCTOR if s_D ≥ tau_D_solo; provisional PATIENT if s_D ≤ tau_notD; otherwise UNCERTAIN; <1 s → UNCERTAIN.
      - **Candidates:** a provisional-PATIENT segment that passes the one-voice check joins the candidate whose centroid cosine ≥ tau_same, or creates one ("A", "B"…).
      - **Replies:** a segment is a reply if it starts within `reply_window_s` after `prev_doctor_end`.
      - **Commit:** a candidate with ≥ learn_seconds and ≥ 1 reply; when several qualify, most replies then most seconds. After 3 doctor turns with no commit, pick most replies then most seconds.
      - **On commit:** the chosen candidate's segments → PATIENT (final), and its fingerprints become the patient templates. Other candidates' segments → OTHER; return them as relabels.
      - **Phase B:** spec §6.4 rule with margin m. A PATIENT segment of ≥3 s with a clear margin is added as a patient template (max 5).
      - Doctor templates are **never** changed.
    - `state() -> VoiceState`
    - `reset()`: clears the patient and the candidates and keeps the doctor.
  - **Fallback**, built only if S1a failed and its fix also failed: `label_by_channel(stereo, ratio_db=6.0) -> Speaker`.
- [ ] **Step 1: Write the tests.**
  - `test_phase_a_rules` and `test_phase_b_rules`, with synthetic scores.
  - `test_commit_after_learn_seconds_with_reply`
  - `test_tv_before_patient_relabelled` (spec L7). Synthetic embeddings: candidate A (TV) has 4 s and no reply; candidate B has 8 s and 1 reply → commit B, relabels = A's sentence ids → OTHER.
  - `test_no_commit_without_reply` (L9)
  - `test_doctor_templates_never_change`
  - `test_s1a_script_all_correct`: on `fixtures/audio/s1a_script_take*.wav` with the real embedder and config → every sentence correct, and `« voix du patient apprise »` reached during line 2.
  - `test_s1a_tv_take_commits_patient` on `fixtures/audio/s1a_tv_take.wav`.
  - `test_noisy_patient_never_doctor` (Review Focus 1): −6 dB volume and SNR 10 dB noise on every PATIENT segment → none labelled DOCTOR.
  - `test_quality_rejects_two_voices`
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS).
- [ ] **Step 5:** `git commit -am "feat: doctor enrollment once, patient learned via candidate voices"`

### Task 14: Session pipeline (Dev A for audio, Dev B for the brain; pair at hours 14–16)

**Files:**
- Create: `src/earshot/pipeline.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: Tasks 4–13.
- Produces **`class Session(cache, transcriber, embedder, client, llm, thresholds, table, session_date, bdpm=None)`**:
  - `async enroll_doctor(audio_clips) -> tuple[bool, str]`: saves to `~/.earshot/doctor.npz`.
  - `async on_segment(seg)`:
    1. transcribe + `VoiceTracker.label` in parallel;
    2. drop the segment if the text is empty;
    3. append the `Sentence`;
    4. apply any relabels: update the sentence speaker and set `final_label`;
    5. `process_sentence`;
    6. notify the scheduler;
    7. recompute verdicts through `View` (label-aware).
  - `async on_scribe_result(run_id, raw)`:
    - ignored if stale, or if `raw` is None;
    - parse, then `line_support` for new or changed lines;
    - `match(... tau_conf=thresholds.tau_conf["q2"])`;
    - bump `note_version`.
  - `async final_check()`: a stub in Tier 1; Task 18 fills it in.
  - `snapshot() -> dict` with `version, mode, status, voice: VoiceState, sentences, lines, actions, verdicts, alerts, note_version, final`.
  - `reset()`: keeps the doctor templates.
  - `subscribe() -> asyncio.Queue`
  - **At session start**, a missing doctor voiceprint → alert `hors cadre : médecin non enregistré`, and the session refuses to start.
- [ ] **Step 1: Write the tests** with fakes.
  - `test_stale_scribe_result_ignored`
  - `test_service_failure_keeps_labelling` (Review Focus 2)
  - `test_reset_keeps_doctor_only` (Review Focus 5)
  - `test_relabel_drops_contributions`: a TV-first sequence → after the commit, the TV sentence's mentions and intake no longer appear in any verdict or alert.
  - `test_missing_doctor_refuses_start`
  - `test_snapshot_versions_increase`
  - `test_empty_transcript_dropped`
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS).
- [ ] **Step 5:** `git commit -am "feat: session pipeline with relabel and versioned snapshots"`

### Task 15: Server and the core screen (Dev A)

**Files:**
- Create: `src/earshot/server.py`, `src/earshot/web/index.html`, `src/earshot/web/app.js`, `src/earshot/web/style.css`
- Test: `tests/test_server.py`

**Interfaces:**
- Consumes: `Session` (Task 14).
- **Routes:**
  - `GET /`
  - `WS /ws` (snapshots)
  - `POST /enroll/doctor?clips=3&seconds=25`
  - `POST /start` `{source, path?}`
  - `POST /stop`
  - `POST /reset`
  - `POST /mode` `{mode}`
- **Screen** (spec §6.11, the Tier 1 parts):
  - **Top bar:**
    - ON/OFF switch (`E`)
    - mic level
    - **médecin ✓**
    - **patient : en attente / apprentissage (progress bar) / apprise ✓ (N s)**
    - service status lights
    - mode
  - **Transcript:**
    - DOCTOR `#1f6feb`; PATIENT `#2da44e`, lighter while provisional; UNCERTAIN amber stripes; OTHER grey, with the reason `voix non retenue comme patient`.
    - A relabelled row animates to grey.
  - **Note:**
    - ON/OFF badges;
    - 🔴 struck through with its reasons;
    - `info` notes in grey;
    - `analyse en cours…` while pending.
  - **Banners:** `dose_alert` (click → RCP quote), false attribution, `hors cadre`, `service_down`.
- [ ] **Step 1: Write the tests** with `TestClient`.
  - `test_ws_sends_snapshot_with_voice_state`
  - `test_reset_endpoint`
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS).
- [ ] **Manual check:** start the server, enroll the doctor, `/start` the demo WAV. Check the colours, the patient progress bar reaching ✓ during line 2, the `E` toggle, and the dose banner.
- [ ] **Step 5:** `git commit -am "feat: server and core demo screen"`

### Task 16: Tier 1 end to end and offline cache (both, hours 16–18)

**Files:**
- Create: `tests/test_e2e.py`, `fixtures/audio/demo_rehearsal.wav`, `fixtures/audio/demo_rehearsal_tv_first.wav`, `fixtures/cache/*`
- Modify: none.

- [ ] **Step 1:** at the demo spot, record the §7.10 script (with the final N), plus one take with a TV clip before line 2. Run each once in `live` mode to fill `fixtures/cache/`.
- [ ] **Step 2: Write the tests.**
  - `test_tier1_reference`, offline, `realtime=False`:
    - speakers D, P, D, P, D, D, P, D;
    - patient voice `learned` before line 3;
    - the after-line-8 verdicts, info and alerts equal `fixtures/demo_scenario.json` `expected.after_8`, **or**, if the live scribe wrote 14 days, `sick_leave` is authorized (spec C7).
  - `test_tier1_tv_first`: the TV rows end up as OTHER, the patient is committed correctly, and the verdicts are identical to `test_tier1_reference`.
- [ ] **Step 3:** `pytest tests/test_e2e.py -v` → PASS. If anything fails, fix the task that owns it; the expected values don't change.
- [ ] **Step 4:** manual live check with the two actors. Check the labels and verdicts, and record the timing (≤2 s per sentence, ≤5 s for a confirmation).
- [ ] **Step 5:** `git add -A && git commit -m "test: Tier 1 end-to-end reference"`. **Gate: Tier 2 can start.**

---

## Tier 2 — robustness and polish (hours 18–24)

### Task 17: Speaker changes, overlaps, per-duration thresholds (Dev A)
**Files:**
- Create: `src/earshot/audio/segment.py`
- Modify: `voice.py` (`label_bucketed`), `pipeline.py`
- Test: `tests/test_segment.py`

**Produces:**
- `sub_segments(seg, left_context) -> list[tuple[float, float, bool]]`: segmentation-3.0, at most 3 s of left context, sub-segments of ≥0.5 s; overlap → UNCERTAIN.
- `label_bucketed(...)`: thresholds per duration, from S1b.

- [ ] **Step 1: Write the tests.** `test_turn_without_pause_split` and `test_overlap_uncertain`, on the S1b clips.
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS); the e2e test still passes.
- [ ] **Step 5:** `git commit -am "feat: sub-segments, overlap, per-duration thresholds"`

### Task 18: Final check, sign, doctor actions, playback, voice picker (Dev A: screen; Dev B: session)
**Files:**
- Modify: `pipeline.py`, `server.py`, `web/*`
- Test: add to `test_pipeline.py` and `test_server.py`

**Produces:**
- `Session.final_check()`: spec §7.9, ≤10 s offline.
- `Session.doctor_action(target, action: Literal["confirm","remove","replace","add","ignore"])`:
  - `replace` swaps a contradicting detail for the doctor's latest value;
  - `confirm` adds the reason `confirmé par le médecin`;
  - every action is logged.
- `Session.pick_patient(candidate_id)`: spec L8, for the Tier 2 picker.
- `can_sign()`.
- Routes: `POST /final`, `POST /doctor-action`, `POST /pick-patient`, `GET /clip/{id}.wav`.
- Screen:
  - ▶ playback on each row;
  - clicking a note line highlights its evidence and plays it;
  - ghost lines for omissions;
  - doctor buttons;
  - « Quelle voix est le patient ? ▶ A ▶ B » when the voice commit is ambiguous;
  - « Fin de consultation » and « Signer et envoyer au dossier », with `N points à vérifier`.

- [ ] **Step 1: Write the tests.**
  - `test_final_check_marks_final`
  - `test_demo_sign_flow`: remove ibuprofen, replace the sick leave (→ authorized, 14 days), confirm the blood test → `can_sign()`
  - `test_pick_patient`
  - `test_clip_endpoint_returns_wav`
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS); extend the e2e test with the sign flow.
- [ ] **Step 5:** `git commit -am "feat: final check, sign flow, doctor actions, playback, voice picker"`

### Task 19: EDS-NLP second check (Dev B)
**Files:**
- Create: `src/earshot/brain/second_check.py`
- Modify: `questions.py`
- Test: `tests/test_second_check.py`

**Produces:** `veto_flags(text, terms) -> tuple[str, ...]`, using the negation, hypothesis and reported-speech qualifiers (check the pipe names at the event). `reported_speech` also counts as a vote for Q4 "autre personne".

- [ ] **Step 1: Write the tests.**
  - "pas d'arrêt de travail" → negation
  - "vous voulez un arrêt ?" → hypothesis
  - "ma mère m'a conseillé de reprendre le travail" → reported_speech
  - "je vous prescris du paracétamol" → ()
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS); re-run `test_rules.py::test_veto` and the e2e test.
- [ ] **Step 5:** `git commit -am "feat: EDS-NLP second check"`

### Task 20: Audit trail (Dev B)
**Files:**
- Create: `src/earshot/infra/trail.py`
- Modify: `pipeline.py`
- Test: `tests/test_trail.py`

**Produces:**
- `Trail(path).append(kind, payload) -> str`
- `verify_trail(path) -> bool`
- `hash = sha256(prev + json.dumps(payload, sort_keys=True, ensure_ascii=False))`, starting from `"0"*64`.
- Entry kinds: those in spec §6.12.

- [ ] **Step 1: Write the tests.** `test_verify_untouched` and `test_verify_detects_edit`.
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS).
- [ ] **Step 5:** `git commit -am "feat: audit trail"`

### Task 21: Live retrieval for drugs outside the table (Dev B)
**Files:**
- Modify: `src/earshot/brain/reference.py`
- Test: add to `tests/test_reference.py`

**Produces:** `async retrieve_limits(substance, rcp_dir, client) -> DrugLimits | None`.
1. Find the posology passage in `reference/rcp/` by substance name, plus semantic search over the cached sections.
2. Have an LLM extract the limits with the quote.
3. Apply the same "number must appear in the quote" filter.
4. Results are marked automatic, so `check_prescription` can only give `to_confirm` for them, never authorized.

- [ ] **Step 1: Write the tests.**
  - `test_retrieved_limits_never_authorize`
  - `test_retrieved_number_not_in_quote_rejected`
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS).
- [ ] **Step 5:** `git commit -am "feat: live retrieval for unknown drugs"`

---

## Tier 3 — bonus: an unknown voice after the commit, the TV (hours 24–26, only if Tiers 1–2 are stable)

### Task 22: OTHER after the commit, AS-norm, TV tag, TV moment (Dev A; Dev B for the reference test)
**Files:**
- Create: `src/earshot/audio/media_tag.py`
- Modify: `voice.py` (`as_norm`, phase B `tau_low` → OTHER + alert), `pipeline.py`, `fixtures/demo_scenario.json`, `tests/test_e2e.py`
- Test: add to `test_voice.py`; create `tests/test_media_tag.py`

**Produces:**
- `as_norm(...)`, against the cohort of other voices from S1b.
- Phase B: both scores below `tau_low` → OTHER, plus the alert `hors cadre : voix inconnue`.
- `tv_score(audio) -> float`: can only push a label down, never up.

- [ ] **Step 1: Write the tests.**
  - `test_tv_after_commit_is_other`
  - `test_media_tag_only_downgrades`
  - e2e with the TV segment between lines 5 and 6 (spec §7.10, bonus): no note line keeps the TV's ibuprofen advice as authorized.
- [ ] **Steps 2–4:** run the tests (FAIL), implement, run the tests (PASS).
- [ ] **Step 5:** `git commit -am "feat: unknown voices after commit, AS-norm, TV tag"`

---

## Rehearsal and freeze (hours 26–36, both)
- [ ] 10 full rehearsals with the live mic. After each, record any wrong label, wrong verdict, or timing problem. Fix only what blocks the demo.
- [ ] Re-record `fixtures/cache/` from the best run, and record a backup video.
- [ ] **Hour 32: code freeze**, then `git tag demo-freeze`.
- [ ] Go through the pre-stage checklist (spec §15, item 8), then the pitch slides and timing (spec §8, §13).
