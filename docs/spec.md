# Earshot: design spec

- **Date:** 2026-10-06
- **Status:** v3, the design agreed in conversation; waiting for the user to review the written version
- **Event:** ESSECKATHON "Secure Horizons", ESSEC Cergy, 10–11 October 2026, 36 hours
- **Track:** 3, "Uncharted Frontiers". Jury: Bpifrance, ESSEC Alumni, UTOPIA (investors and business people)
- **Team:** 2 developers

**Revision history**
- **v3 (2026-10-06):**
  - Earshot works inside a defined operating domain: a closed world (§2.2). Anything outside it is marked « hors cadre » ("out of scope") and handed back to the doctor.
  - The doctor's voice is recorded **once**. The patient's voice is **learned automatically** through candidate voices: Earshot commits to the voice that replies to the doctor, so a TV or another voice heard first is set aside (§6.4).
  - New **drug and dose reference** (retrieval: "find by meaning, decide on numbers", §6.8), with dose checks.
  - New source type: **advice from a third party reported by the patient**.
  - New, more natural **8-line demo script**: honest confusion, not fraud (§7.10).
  - Edge cases are regrouped into: inside the domain / departures we can detect / conditions of use (§9).
- **v2.1 (2026-10-06):** the priority is a working, clean demo; features are split into tiers.
- **v2 (2026-10-06):** reviewed against industry practice and research. Added an action log with an omission check, offers that need the patient's acceptance, and a final check at the end of the consultation. A microphone worn by the doctor was not adopted.
- **v1 (2026-10-06):** first design.

---

## 1. Summary

AI medical scribes listen to a consultation and write the medical note. More and more, they also draft the *actions*: prescriptions, sick notes (*arrêts de travail*), certificates, referrals, test orders. They record *what* was said. They never check *who had the authority to say it*.

In a real consultation, the patient often repeats advice from someone else ("my mother told me to…"), and the doctor then corrects it. A scribe can turn that advice into a prescription. A busy doctor who signs without reading closely then makes it real.

**Earshot** sits between the scribe and the medical record. It enforces one rule: **an action in the record must trace back to something the doctor actually said, in their own voice, and meant as a decision.** Every action line is marked ✅ authorized, 🟠 doctor to confirm, or 🔴 blocked. Each mark comes with the reason and the sentences behind it, which can be played back.

Earshot also:
- flags what the doctor decided but the note left out;
- checks doses against the official drug information ("3 fois 1000 mg" ↔ "3 g par jour");
- warns the doctor when the patient reports taking too much of a drug.

It works within a defined **operating domain**. Outside that domain it doesn't guess: it hands the decision back to the doctor.

Pitch line: *« Sa mère vient d'écrire l'ordonnance. »* ("His mother just wrote the prescription.") Earshot catches it.

## 2. Intent, constraints, success criteria

### What the user decided
- **Track 3.** It needs real novelty and a short, marketing-style demo.
- **Priority: a working, clean demo.** Two people talk, and Earshot knows exactly who is speaking. The TV attack is a bonus.
- **The consultation is a closed world.** We scope everything from its known structure, so the system doesn't have to handle unexpected situations (§2.2).
- **Preparation before the event, product code during the 36 hours.** Code written for this week's tests is throwaway. Recordings, results and reference data are kept (§12).
- **Team:** 2 developers. **Demo and screen:** in French. **Code:** in English.
- **Checking is live.** A final check runs at the end of the consultation.
- **Jev** is used where it fits, with an LLM as fallback.
- **v2 additions:** the action log with an omission check; offers that need the patient's acceptance; the end-of-consultation check. **No** microphone worn by the doctor.
- **v3 additions:**
  - the operating domain;
  - the doctor's voice recorded once and the patient's voice learned;
  - the drug and dose reference, including the semantic dose matching;
  - advice from a third party;
  - the natural 8-line script.
- **Everything is written in detail,** including edge cases and known limits.

### Assumptions
- **Hardware:** one Mac laptop, with internet access for the cloud services.
- **Actors:** two team members play the doctor and the patient.
- **Data:** all demo data is invented. No real patient data is used.

### 2.1 Feature tiers
Build in tier order. **Don't start a tier until the one before runs end to end in replay mode.**

| Tier | Feature | Components |
|---|---|---|
| **1: must work cleanly** | The doctor's voice is recorded once and loaded at the start. The patient's voice is learned through **candidate voices**, and Earshot commits to the one that replies to the doctor (a TV heard before the patient becomes OTHER retroactively). Each sentence is labelled DOCTOR / PATIENT / UNCERTAIN live. | [1] [2] [3] [4] |
| 1 | A naive scribe writes the note and the actions | [5] |
| 1 | Per-sentence questions Q1–Q6 feed the action log; rules give ✅/🟠/🔴 with reasons; third-party advice is detected; false-attribution banner; spoken confirmation | [6] [7] [9] [10] |
| 1 | Drug and dose reference for the demo drugs (lookup table): dose annotations, alerts for overdoses the patient reports, flags when a prescription is above the maximum | [8] |
| 1 | Screen: transcript coloured by speaker, "patient's voice learned" indicator, note with badges, ON/OFF switch, banners | [11] |
| 1 | Replay from a file and offline mode | [1] [13] |
| **2: robustness and polish** | Speaker changes without a pause, overlapping speech, thresholds that depend on duration | [4] |
| 2 | Click a line to play its audio; final check; « Signer »; omissions; doctor buttons (Confirmer / Retirer / Remplacer / Ajouter / Ignorer) | [11] [10] |
| 2 | EDS-NLP second check; audit trail; live retrieval for drugs outside the lookup table | [6] [12] [8] |
| **3: bonus** | A third voice (the TV) becomes « hors cadre : voix inconnue »; AS-norm against recordings of other voices; optional YAMNet "TV" tag; the TV moment in the demo | [4] [11] |

### 2.2 Operating domain (the closed world)
A consultation is predictable. Earshot is built for the following domain. **Inside it, Earshot is exact. Outside it, Earshot doesn't guess.**

**What is known before anyone speaks:**

| Variable | Value in the domain | Where it comes from |
|---|---|---|
| Doctor | Identity and voiceprint | Logged in for the day (a button in the demo); voice recorded once (§6.4) |
| Patient | An adult who came alone | The appointment |
| People speaking in the room | **2** | The appointment type |
| Start and end | Opening the patient's record, then signing | The doctor's software (buttons in the demo) |
| Room and microphone | One room, one laptop microphone in a fixed position | Setup |
| Language | French | Setup |
| Possible actions | 6 types: prescription, sick note, certificate, referral, test order, renewal | A fixed list |
| Drugs and doses | Drugs in the reference (§6.8), adult dosage | Reference data |
| Who can do what | The doctor decides. The patient describes, reports what others advised, and accepts or refuses. | The rules (§7) |

**How a consultation unfolds:**
1. Greeting
2. "Qu'est-ce qui vous amène ?" ("What brings you here?")
3. Questions
4. Examination
5. Conclusion and decisions
6. Paperwork
7. Goodbye

The patient's voice is learned from their first answer (§6.4). The consultation steps are never used to decide authority.

**Leaving the domain in a way Earshot can detect → 🟠 or an alert « hors cadre : … ».** Earshot states the reason and hands the decision to the doctor:
- a third voice that matches neither the doctor nor the patient (Tier 3 shows this);
- two people speaking at once, or a turn too short to identify;
- an action outside the 6 types;
- a drug that isn't in the reference;
- a child's or weight-based dosage;
- the doctor's voice not recognised at the start: Earshot stops and says so;
- the patient's voice couldn't be learned.

**Leaving the domain in a way Earshot can't detect = conditions of use.** These are stated, the way an autonomous car states the conditions it was designed for:
- no recording or AI clone of the doctor's voice is played;
- the doctor speaks only to the patient (no phone calls during the consultation);
- what the patient says about their symptoms and history is their own responsibility;
- the doctor is not complicit.

Under the EU Medical Device Regulation (MDR), a device must declare its intended purpose and conditions of use. This domain *is* that declaration.

### Success criteria
1. **(Tier 1)** In a live two-person consultation, **every** sentence of the demo script gets the correct DOCTOR / PATIENT label. No patient sentence is ever labelled DOCTOR. The screen shows « voix du patient apprise » ("patient's voice learned") during line 2.
2. **(Tier 1)** When switched ON, the note shows:
   - ibuprofen 🔴: withdrawn by the doctor, advice from a third party;
   - a sick note that contradicts the doctor 🔴 (if the scribe got it wrong);
   - paracetamol ✅, annotated "matches the usual dosage";
   - the conditional blood test 🟠;
   - an alert for the doctor about the dose the patient reported taking.
3. **(Tier 1)** The demo still works without venue wifi (offline replay) and without a working microphone (replay from a file).
4. **(Tier 2)** Clicking a line plays the voices behind it. « Fin de consultation » → corrections → « Signer ».
5. **(Tier 3, bonus)** A sentence from the TV is marked « hors cadre : voix inconnue », and anything it adds to the note is removed.
6. The jury leaves with a credible startup story.

## 3. Problem and evidence

| Fact | Source |
|---|---|
| Doctolib's consultation assistant: more than 6 million consultations. It drafts notes and letters and handles renewals, certificates and sick notes. It warns that its suggestions "may contain elements not mentioned during the consultation". | [Doctolib](https://about.doctolib.fr/news/intelligence-artificielle-doctolib-lance-lassistant-de-consultation/), [Doctolib help](https://doctolib.zendesk.com/hc/fr/articles/37194303903892-G%C3%A9n%C3%A9rer-automatiquement-un-courrier-avec-l-Assistant-de-consultation) |
| Nabla Copilot turns conversations into prescriptions and letters, and has thousands of French doctors as users. | [TechCrunch](https://techcrunch.com/2023/03/14/nabla-a-french-digital-health-startup-launches-copilot-using-gpt-3-to-turn-patient-conversations-into-actionable-items/), [Egora](https://www.egora.fr/actus-pro/sante-numerique/gagner-entre-une-et-deux-heures-par-jour-deux-plateformes-utilisent-lia) |
| Abridge drafts orders from "clinicians' spoken intent", with no mention of checking who spoke. | [Abridge](https://www.abridge.com/blog/orders-real-time-clinical-documentation) |
| An audit of 3 commercial scribes found a verified failure in 31.3% of 565 notes. Groups of failures included: alternative options recorded as issued prescriptions (14), a withdrawn device recorded as delivered (11), planned tests written up as done (32), sick-note plans dropped (16). | [arXiv 2608.31017](https://arxiv.org/abs/2608.31017) |
| LLM judges catch additions (0.79–0.94) but are close to chance on omissions (0.50–0.63). Listing what should be there, then checking each item, recovers part of it. | [arXiv 2608.31016](https://arxiv.org/abs/2608.31016) |
| Background noise raised the word error rate by 0.71 points but nearly doubled unsafe scribe outputs. | [arXiv 2606.05909](https://arxiv.org/abs/2606.05909) |
| AWS HealthScribe: role tags and links back to the transcript, US English only; the links are "probabilistic". | [AWS service card](https://docs.aws.amazon.com/ai/responsible-ai/aws-healthscribe/overview.html) |
| Assurance Maladie (French national health insurance): €723M of fraud stopped in 2025, of which €49M was fake sick notes. | [ameli.fr](https://www.ameli.fr/assure/actualites/en-2025-l-assurance-maladie-detecte-et-stoppe-723-millions-d-euros-de-fraudes) |
| Scribes are medical devices under the MDR. Tandem became the first scribe certified Class IIa. The UK regulator (MHRA) issued guidance in July 2026. AI Act high-risk obligations for medical devices start in August 2028. | [Tandem](https://tandemhealth.ai/resources/news/tandem-s-ai-scribe-is-now-mdr-class-iia-certified), [MHRA](https://www.insideeulifesciences.com/2026/08/06/new-uk-guidance-clarifies-medical-device-status-of-ai-scribes/) |
| Products are weak at telling who said what:<ul><li>Dragon Copilot's multilingual (French) transcripts "don't indicate who is speaking".</li><li>Granola "cannot distinguish the individuals" sharing one device.</li><li>Zoom attributes audible podcasts to the signed-in user.</li></ul> | [Dragon](https://support.microsoft.com/en-us/dragon-copilot/physicians/multilingual-conversations), [Granola](https://docs.granola.ai/help-center/taking-notes/speaker-attribution), [York U.](https://lthelp.yorku.ca/introduction-to-zoom-ai-companion) |

**How Earshot differs from existing products:** linking a note to its evidence (HealthScribe, Abridge) answers *"where did this sentence come from?"*, for a human to review. Earshot answers *"did the person who said it have the authority, was it really their voice, and does the dose match the official drug information?"*, and **enforces** the answer.

## 4. Scope

**In:**
- Doctor's voice recorded once.
- Patient's voice learned automatically.
- Live speaker labels from the voice, one per sentence.
- A naive scribe.
- Questions Q1–Q6, plus the EDS-NLP second check (Tier 2).
- Action log and note matcher.
- Authority rules, omissions, false attribution, advice from a third party.
- Drug and dose reference with dose checks.
- Confirmation by speaking or by clicking.
- Final check.
- Screen with playback.
- Audit trail.
- Replay from a file and offline mode.
- Pre-event tests.

**Out:**
- Connection to a real patient-record system.
- Cryptographic signatures.
- More than one person besides the doctor (Tier 3 only *detects* a third voice).
- Teleconsultation audio.
- Separating overlapping speech.
- Detecting a replayed or cloned voice.
- Children's or weight-based dosing.
- Cumulative doses across a patient's own intake and a prescription.
- Interaction checks between drugs.
- Mobile apps.
- Languages other than French.
- A microphone worn by the doctor (roadmap).

## 5. Architecture

```
mic / WAV → [1 capture] → [2 sentence cutter] → sentence audio (kept in memory for playback)
                                               ├→ [3 transcriber] → French text + word timestamps
                                               └→ [4 voice check] → DOCTOR / PATIENT / UNCERTAIN (+ patient voice learning)
                     Sentence {id, start, end, text, words, speaker, scores}
                        ├→ [5 naive scribe] (the victim) → scribe note {lines, actions}
                        └→ [6 sentence questions Q1–Q6 + second check] → events, mentions, claims, intake reports
                                       → [9 action log] (append-only)
     [7 normalizer] → standard dose quantities      [8 drug reference] → limits + quotes (lookup; Tier 2 live retrieval)
               [10 note matcher]: scribe note × log × reference → verdicts + omissions + alerts
                       → [11 screen] (WebSocket)      → [12 audit trail]
All external calls go through [13 cache] (live / offline). [14 pipeline state] orders everything.
```

**Stack:** Python 3.11+, FastAPI and WebSockets, one HTML/JS page with no framework, one Mac.

### 5.1 Data passed between components
These are fixed in the first two hours of the event, then left unchanged.

```text
Sentence { id, start, end, text, words: [{w, start, end}], speaker: "DOCTOR"|"PATIENT"|"OTHER"|"UNCERTAIN",
           scores: {doctor, patient?}, media_tag: "TV"|null }       # OTHER is used only in Tier 3

ActionEvent { seq, sentence_id, speaker, kind: "decision"|"offer"|"alternatives"|"withdrawal"|"conditional"|"accept"|"refuse",
              key, details, confidence, veto: [str] }

Mention { sentence_id, speaker, key, details, source: "self"|"third_party"|"doctor_claim" }   # any sentence relevant to a key

Claim { sentence_id, key, details, attributed_to: "doctor"|"third_party" }

DoseQuantity { substance, per_intake_mg?, intakes_per_day?, daily_mg?, min_interval_h?, duration_days? }   # standard form, §6.7

DrugLimits { substance, population: "adult", usual_daily_mg?, max_daily_mg?, max_per_intake_mg?, min_interval_h?,
             quote: str, source_url: str }                          # §6.8

IntakeReport { sentence_id, substance, daily_mg, window_h: 24 }     # the patient says they took X

ScribeAction { type: "prescription"|"sick_leave"|"certificate"|"referral"|"test_order"|"renewal",
               fields, normalized, key, text }

NoteLine { id, section: "reason"|"history"|"exam"|"conclusion", text }

Verdict { target, status: "authorized"|"to_confirm"|"blocked"|"missing"|"pending",
          reasons: [str], info: [str], evidence_ids: [int], provisional: bool }

Alert { kind: "false_attribution"|"dose_alert"|"out_of_domain"|"ambiguous_action"|"service_down"|"enrollment",
        text, sentence_id? }

VoiceState { doctor_loaded: bool, patient: "waiting"|"learning"|"learned", patient_seconds: float,
             candidates: [{id: "A"|"B"|…, seconds: float, replies: int, chosen: bool}] }

Sentence.final_label: bool       # false while the label is still provisional (PATIENT before the commit)
```

## 6. Components in detail

### 6.1 [1] Capture
- **Input:** the default microphone, 16 kHz, mono, through the exact audio chain used on stage. Or a WAV file played back in real time.
- **Output:** 32 ms chunks. Each sentence's audio is kept in memory until the session is reset, so it can be played back.
- **Fallback if voice recognition fails in S1a and the fix also fails:** a stereo input with one lapel microphone per person. The louder channel then decides who is speaking.

### 6.2 [2] Sentence cutter
- **Method:** Silero VAD, streaming.
- **Cuts:** a sentence ends after 600 ms of silence. Speech shorter than 250 ms is discarded. Sentences are capped at 15 s.

### 6.3 [3] Transcriber
- **Primary:** Mistral Voxtral, French, one sentence at a time, with word timestamps. S3 checks the endpoint, the model and whether timestamps come back.
- **Fallback:** local Whisper (`word_timestamps=True`).
- **Vocabulary hints:** a fixed list of drug names (≤100 terms) if S3 shows it helps. **Never built from the note.**

### 6.4 [4] Voice check: doctor recorded once, patient learned automatically
**The principle:** only the doctor's voice gives authority, so only the doctor needs a voiceprint recorded in advance. The patient's voice is learned during the consultation and never gives authority, so a mistake about it can never create a false ✅.

**Model:**
- **Default:** SpeechBrain ECAPA-TDNN. It turns a speech clip into 192 numbers, an L2-normalized "embedding" that acts as a voice fingerprint.
- **Alternative:** WeSpeaker ResNet34, if S1a finds it better.

**Doctor, recorded once:**
- **When and where:** at setup, at the demo spot, through the demo microphone.
- **What:** 2–3 readings of 20–30 s each. Each reading becomes one template.
- **Quality check, per reading:**
  - at least 15 s of speech;
  - one voice only: every 1.5 s window must match the reading's average fingerprint at ≥ τ_cons.
- **Storage:** saved locally on the laptop (`~/.earshot/doctor.npz`), with the doctor's consent.
- **Loading:** when the session starts. If it's missing, the screen shows the alert « hors cadre : médecin non enregistré » ("outside scope: doctor not enrolled").
- **Never updated during a consultation.**

**Patient, learned automatically through candidate voices:**
- **Phase A: before the patient's voice is chosen.** Earshot can only compare against the doctor (s_D):
  - s_D ≥ τ_D_solo (stricter than in phase B) → **DOCTOR**;
  - s_D ≤ τ_notD → "not the doctor" → **PATIENT (provisional)**, shown in light green;
  - in between, or a segment shorter than 1 s → **UNCERTAIN**.
- **Candidate voices.** Every "not the doctor" segment that passes the one-voice check is grouped by voice (online clustering):
  - **Grouping:** a segment joins an existing candidate if its fingerprint is close enough to that candidate's average (cosine ≥ τ_same, from S1a). Otherwise it starts a new candidate: A, B…
  - **What each candidate tracks:** total speaking time, and how many **replies to the doctor** it gave. A reply is a segment that starts ≤ 2.0 s after a DOCTOR segment ends.
- **Choosing the patient (commit):**
  - **Rule:** commit to the candidate with ≥ 6 s of speech (exact figure from S1a: 4, 6 or 8 s) and ≥ 1 reply to the doctor. If several candidates qualify, the one with the **most replies** wins, then the one with the most seconds.
  - **Why this works:** in a consultation, the patient is the voice that *answers the doctor*. A TV, a radio or a voice in the corridor talks on its own schedule. This is a **turn-taking** signal, measured on timing, not on the words. It only ever chooses between *patient* and *other*, and never gives anyone the doctor's authority.
  - **What happens on commit:**
    - that candidate's segments become the patient's templates (state `learned`);
    - its segments become **PATIENT** (final);
    - segments from the **other candidates** become **OTHER**, with the reason « voix non retenue comme patient » ("voice not kept as the patient"), **retroactively**. Their mentions, claims and intake reports stop counting (§6.14). The screen shows those rows turning grey.
  - **Screen:** a progress bar, then « voix du patient apprise (N s) ✓ » ("patient's voice learned").
  - **When it happens:** in a real consultation, the commit happens during the patient's answer to "qu'est-ce qui vous amène ?" ("what brings you here?").
- **Ambiguity:** if no candidate qualifies, or two are tied, after 3 doctor turns:
  - **Tier 1:** commit to the candidate with the most replies, then the most seconds.
  - **Tier 2:** ask the doctor once, « Quelle voix est le patient ? ▶ A ▶ B » ("Which voice is the patient?"). One click.
- **Phase B: after learning.** Both templates are compared, s_D and s_P:
  - s_D ≥ τ_D and s_D − s_P ≥ m → **DOCTOR**;
  - s_P ≥ τ_P and s_P − s_D ≥ m → **PATIENT**;
  - otherwise, or a segment shorter than 1 s → **UNCERTAIN**.
- **The patient's voice keeps improving:** a PATIENT segment of ≥ 3 s with a clear margin is added as an extra template, up to 5 templates. **The doctor's templates are never updated.**
- **Thresholds:** τ_D_solo, τ_notD, τ_D, τ_P, m, τ_same and τ_cons come from S1a. They are set so that **no patient segment is ever labelled DOCTOR, and no doctor segment ever joins a candidate**.

**Text is never used.** No LLM, DiarizationLM or provider speaker labels are used to decide who spoke.

**Tier 2:**
- pyannote segmentation-3.0 splits a sentence wherever the speaker changes, and marks overlapping speech UNCERTAIN.
- The text is split using word timestamps.
- Thresholds depend on segment length (<1 s, 1–2 s, 2–4 s, ≥4 s; values from S1b).

**Tier 3 (bonus):**
- **A new voice after the commit:** in phase B, if both s_D and s_P are below τ_low → OTHER, plus the alert « hors cadre : voix inconnue » ("outside scope: unknown voice"). Its sentences can't add anything to the note.
- **A voice heard before the patient (L7)** is already handled in Tier 1 by the candidate voices.
- AS-norm uses a set of "impostor" recordings: teammates, plus French TV played through a speaker.
- Optional YAMNet "Television/Radio" tag. It can only downgrade a label, never upgrade one.

### 6.5 [5] Naive scribe (stands in for today's products)
- **Model:** one LLM, Mistral or Claude on Bedrock (S5 decides).
- **Input:** the transcript with **neutral speaker labels** ("Locuteur 1/2", "Speaker 1/2", numbered by first appearance). Earshot's labels are never shown.
- **Prompt:** typical of real products. It writes the note and drafts the prescriptions and paperwork, as JSON `{lines, actions}`, one fact per line.
- **When it runs:**
  - after a pause of ≥ 1.2 s, and at most every 5 s;
  - the most recent run wins, older results are thrown away;
  - each run is stamped with the last sentence id it saw.
- **Earshot never trusts the scribe's structure.** It normalizes and assigns keys itself (§6.10).

### 6.6 [6] Sentence questions and the second check
**Principle: models read meaning, code decides authority.** Who spoke comes only from [4]. Each question concerns **one target sentence**.

**Questions.** Jev answers first. The LLM is the fallback, used only when Jev's confidence is below τ_conf for that question.
- **Q1, relevance.** A cheap code filter runs first; only if it matches does the model confirm "which action (type and target)?". The filter matches drug names (from the reference and its synonyms) and the words « arrêt », « repos », « reprendre le travail », « certificat », « ordonnance », « radio », « prise de sang », « courrier », « renouvel* ».
- **Q2, kind of statement** (DOCTOR and UNCERTAIN sentences): decision / offer / alternatives / withdrawal / conditional / mention / reformulation (§7.2), with a confidence score.
- **Q3, details.** **This is code, not a model.** `extract_details` (§6.7) reads the sentence's own words. The LLM only steps in for unusual wording, and every number it returns must then be found in the sentence by the normalizer.
- **Q4, who recommended it** (PATIENT and UNCERTAIN sentences): "Does this sentence say that someone advised, prescribed or decided something? Who: *the doctor here* / *someone else* / *nobody*?"
  - *The doctor here* → a Claim attributed to the doctor, checked for false attribution (§7.6).
  - *Someone else* ("ma mère m'a conseillé…", "mon ancien médecin me donnait…") → Mentions with `source = third_party` (§7.7).
- **Q5, answer to an offer** (PATIENT and UNCERTAIN sentences within 3 sentences of an open offer): accept / refuse / neither.
- **Q6, reported intake** (PATIENT and UNCERTAIN sentences): "Does the patient say they took a drug? How much, and when?" (yes/no). The amounts are extracted by code and become an `IntakeReport` (§6.8).

**How the calls are batched (decided in Phase 0, `prompts.md` §2):** Q1 and Q2 are merged into one choice per candidate action, with the 7 kinds plus `pas_concerné` ("not about it"). Every question about one sentence goes in **a single Jev call**, so the input is billed once.

**Context and protection:**
- Each question sees the target sentence plus the 3 sentences before it, inside randomized delimiters, with speaker labels set by code. This is "spotlighting".
- **Details only count when they appear in the target sentence's own words.**

**Second check, without an LLM (Tier 2):** EDS-NLP qualifiers for negation, hypothesis and reported speech, applied to the action mention.
- If one of them fires while Q2 says decision or offer → at best 🟠.
- The reported-speech qualifier also supports Q4's "someone else".

**Wording:** effort goes into how the questions are worded (§17: wording mattered more than adding models) and into the S4 test set.

### 6.7 [7] Normalizer and standard dose quantities (code)
- **Numbers written in words:** "demi" is handled first, then text2num.
- **Doses** are converted to mg ("1 g" = "1000 mg" = "mille milligrammes"; "zéro virgule cinq milligramme" = 0.5 mg).
- **How often:** "trois fois par jour" = "3 fois/j" = "matin, midi et soir" (MORN/NOON/EVE) = "toutes les 8 heures" → 3 times a day. "Matin et soir" → 2. "Toutes les 6 heures" → 4.
- **Durations:**
  - "X jour(s)", "une semaine" = 7, "deux semaines" = 14, "quinze jours" = 15;
  - "un mois" stays in months;
  - relative dates in our own code: "jusqu'à vendredi", "lundi", "dans trois jours", counted from the session date.
- **Counts × strength:** "quatre, des 400" or "5 Doliprane 1000" → count × the product's strength. The strength comes from the reference (§6.8). When it's ambiguous (a product sold in several strengths and none stated), the detail is missing.
- **Standard form: `DoseQuantity`.**
  - It holds the amount per intake (`per_intake_mg`), intakes per day (`intakes_per_day`), the daily total (`daily_mg` = amount per intake × intakes per day, or stated directly as in "3 g par jour"), the minimum interval (`min_interval_h`) and the duration in days (`duration_days`).
  - **"3 fois 1000 mg", "1 g trois fois par jour", "1000 mg toutes les 8 heures" and "3 g par jour" all give `daily_mg = 3000`.**
- **Not used:** NVIDIA NeMo text normalization (it failed to install on a Mac and gave wrong results in testing).

### 6.8 [8] Drug and dose reference ("find by meaning, decide on numbers")
**Why not compare meanings directly:** an embedding model sees "3 g par jour" and "4 g par jour" as nearly the same sentence, so it can't tell a normal dose from an overdose. Meaning is used **only to find** the right passage. **Decisions are always made on numbers.**

- **Data, prepared before the event (S8):**
  - The French public drug database (BDPM): brand → active substance, available strengths, pharmaceutical form.
  - For each drug used in the demo (at least paracetamol, ibuprofen, tramadol and the usual synonyms), the **dosage section (section 4.2) of its official product summary (RCP)**, fetched from the BDPM site. How to retrieve it gets checked in S8.
- **Extracting limits, once, offline:**
  - An LLM reads each dosage section and fills in a `DrugLimits` record for adults: usual and maximum daily dose, maximum per intake, minimum interval, plus the **exact quote**.
  - **The loader rejects any limit whose number doesn't appear in the quote** (after normalization). Then a human reads the table. The result is `reference/drug_limits.json` (data).
- **During the consultation (Tier 1), a simple lookup:** `limits(substance) -> DrugLimits | None`. It's fast, predictable and checkable.
- **Tier 2, live retrieval for drugs outside the table:**
  - find the dosage passage by substance name plus semantic search over the cached product-summary texts;
  - extract the limits with the same check;
  - the result is marked « référence extraite automatiquement » ("reference extracted automatically") and can only lead to 🟠, never ✅.
- **The checks (code):**
  1. **A prescription within the limits:** an `info` note on the verdict, « conforme à la posologie usuelle (3 g/jour, RCP) » ("matches the usual dosage") or « dans les limites (max 4 g/jour, RCP) » ("within the limits").
  2. **A prescription above the maximum**, or an interval shorter than the minimum → 🟠 « dose au-dessus du maximum (RCP : X) » ("dose above the maximum"). The doctor may have meant it, so they confirm.
  3. **What the patient reports taking** (`IntakeReport`) is above the maximum → alert `dose_alert`: « Prise rapportée : <substance> <daily_mg> mg en 24 h — au-dessus du maximum (RCP : X) » ("reported intake… above the maximum"). Clicking it shows the RCP quote. It **informs**; it doesn't block.
  4. **A drug not in the reference** → 🟠 « hors cadre : médicament inconnu » ("outside scope: unknown drug").
  5. **A child's or weight-based dosage** → 🟠 « hors cadre : posologie pédiatrique » ("outside scope: paediatric dosage").

### 6.9 [9] Action log (append-only)
- **Events from the doctor:** a DOCTOR (or UNCERTAIN) sentence that Q1 finds relevant and Q2 classes as decision / offer / alternatives / withdrawal / conditional → an event with its key and its verified details.
- **Patient answers:** accept or refuse (Q5) from a PATIENT or UNCERTAIN sentence about the most recent open offer → an event under that offer's key.
- **Everything else** goes into separate lists: `Mention`s (every relevant sentence, with its source), `Claim`s and `IntakeReport`s.
- **Keys** are built in code: `prescription:<substance>`, `sick_leave`, `certificate:<kind>`, `referral:<specialty>`, `test_order:<test>`, `renewal:<substance>`.
- **No edits and no deletes.** The state of each key is rebuilt by replaying its events.

### 6.10 [10] Note matcher
- **After each scribe run:** parse it, normalize, assign keys, then give a verdict for each action (§7.4) using the log and the reference (§6.8).
- **Duplicate key** → 🟠 « action ambiguë » ("ambiguous action").
- **Unknown type** → 🟠 « hors cadre : action non reconnue » ("outside scope: unrecognized action").
- **Note lines:** provenance is checked (§7.1).
- **Omissions:** a key whose state is "authorized intent" but has no scribe action → `missing` « manquant dans la note » ("missing from the note"). Provisional live, firm after the final check.

### 6.11 [11] Screen
One HTML/JS page in French, fed by WebSocket. Each update is a full versioned snapshot.

- **Top bar:**
  - the **Earshot ON/OFF** switch (key `E`);
  - microphone level;
  - **doctor ✓** (voice loaded);
  - **patient: waiting / learning (progress bar) / learned ✓ (N s)**;
  - one status light per service;
  - the mode.
- **Left, the transcript:**
  - rows coloured DOCTOR blue, PATIENT green, UNCERTAIN amber stripes (OTHER grey in Tier 3);
  - ▶ plays the sentence (Tier 2).
- **Right, the note**, in five sections: Motif (reason), Anamnèse (history), Examen (exam), Conclusion, Prescriptions et actes (prescriptions and actions).
  - **OFF:** no badges.
  - **ON:**
    - ✅/🟠/🔴 badges (provisional ones drawn as outlines);
    - 🔴 struck through, with the reason underneath;
    - `info` notes in grey (e.g. « conforme à la posologie usuelle »);
    - grey ghost lines for omissions;
    - clicking a line highlights its evidence and plays it (Tier 2).
  - **Doctor buttons (Tier 2):**
    - « Confirmer » on 🟠;
    - « Retirer » (remove) on 🔴;
    - « Remplacer par la décision du médecin » on a 🔴 contradiction: replaces the detail with the doctor's own value;
    - « Ajouter » (add) / « Ignorer » (ignore) on omissions.
- **Banners:**
  - dose alert, with the RCP quote on click;
  - false attribution;
  - « hors cadre : … »;
  - ambiguous action;
  - a service down.
- **Buttons:** « Fin de consultation » (end of consultation) and « Signer et envoyer au dossier » (sign and send to the record). Signing is enabled only after the final check, with no 🔴, 🟠 or missing item left; otherwise the button reads « N points à vérifier » ("N points to check").
- **The switch only changes what is shown.**

### 6.12 [12] Audit trail (Tier 2)
- **Format:** JSONL, chained by hash: `hash = sha256(prev_hash + canonical_json(payload))`.
- **Entry kinds:** enrollment, voice_learned, sentence, event, intake, scribe_run, verdict_change, doctor_action, final_check, alert, sign.
- **Checking:** `verify_trail()`.
- **Limit:** it detects tampering, but it is not a signature.

### 6.13 [13] Cache and offline mode
- **Every external call** goes through `cached_call(service, model, input)`.
- **Two modes:**
  - live: call the service and store the answer;
  - offline: read only; a missing answer is shown as an error.
- **Replay from a file plus offline mode** gives a deterministic demo. A live microphone always needs the network.

### 6.14 [14] Pipeline state and concurrency
- **One event loop, one state object:** sentences, voice state, log, reference, note, verdicts, alerts.
- **Tasks run in parallel; their results go through one queue,** applied in order.
- **Versioning:** `note_version`, `log_seq` and the stamp on each verdict; stale results are thrown away.
- **Full snapshots** go to the screen.
- **Time budgets:**
  - sentence labelled ≤ 2 s;
  - patient's voice learned by the end of their first answer;
  - spoken confirmation shown ≤ 5 s;
  - final check ≤ 10 s.
- **Reset:** clears the sentences, log, note, verdicts, candidates and the **patient's** voiceprints. The doctor's voiceprint stays loaded.
- **Labels can change after the fact (commit).** The action log stays append-only. Its derived state (mentions, claims, intake reports, where each note line came from) is always recomputed from each sentence's **current** label. When a sentence becomes OTHER, its contributions drop out at the next recomputation, and no entry is deleted. Doctor events are never affected: they only come from DOCTOR sentences, and a DOCTOR label is never changed.

## 7. Authority rules (code)

### 7.1 Who may put what into the note
| Section | Accepted from |
|---|---|
| Motif, Anamnèse | PATIENT or DOCTOR. Third-party advice is accepted as **history**: « rapporté par le patient » ("reported by the patient"). |
| Examen, Conclusion/diagnosis | DOCTOR only |
| **Actions** | **DOCTOR only**, through the action log |
| Anything | Never OTHER. An UNCERTAIN sentence never counts as the doctor's authority. |

- A diagnosis backed only by the patient → 🔴 « diagnostic issu du patient » ("diagnosis that came from the patient").
- A line backed only by OTHER → 🔴 « hors cadre : voix inconnue ».

### 7.2 Kinds of statement
**Doctor (Q2):**
- `decision`: authorizes, if the details check out (§7.3).
- `offer`: authorizes only once the patient accepts or the doctor decides later.
  - no answer → 🟠;
  - refused → 🔴.
- `alternatives`: never authorizes a single item. It stays 🟠 until a later decision picks one.
- `withdrawal`: cancels earlier support → 🔴.
- `conditional`: 🟠.
- `mention` and `reformulation`: no event.

**Patient (Q5), only in reply to an open offer:** accept or refuse, from PATIENT or UNCERTAIN, never OTHER. These carry no details.

### 7.3 Details rule
- **What counts:** a detail counts only if it is **stated in the doctor's own words** (a decision or offer event for that key). The **latest** value wins.
- **How values are compared:** as standard quantities (§6.7). So « trois fois mille milligrammes » equals « 1 g × 3/jour ».
- **Outcomes:**
  - same value → fine;
  - different value → 🔴 « détail contredit le médecin (médecin : X) » ("detail contradicts the doctor; doctor said X");
  - said only by the patient → 🟠 « détail dit par le patient » ("detail said by the patient");
  - said by a third party (reported) → 🟠 « détail issu d'un conseil d'un tiers » ("detail from third-party advice");
  - said by nobody → 🟠 « détail non prononcé » ("detail never said").
- **Status details** (planned vs done) that differ → 🟠 « statut différent » ("different status").

### 7.4 Verdict for one scribe action (key k)
1. **No DOCTOR event for k:**
   - if an UNCERTAIN event would authorize it → 🟠 « voix incertaine » ("uncertain voice");
   - otherwise → 🔴 « aucune phrase du médecin » ("no sentence from the doctor").
   - If k also has a third-party Mention, add « conseil d'un tiers rapporté par le patient » ("third-party advice reported by the patient").
2. **Look at the latest DOCTOR event for k:**
   - withdrawal → 🔴 « retiré par le médecin » ("withdrawn by the doctor"), plus the third-party reason if it applies;
   - alternatives → 🟠 « alternative proposée, pas choisie » ("alternative offered, not chosen");
   - conditional → 🟠 « ordonnance conditionnelle » ("conditional order");
   - offer + accept → treated as a decision; offer + refuse → 🔴 « proposition refusée » ("offer refused"); offer with no answer → 🟠 « proposition non acceptée » ("offer not accepted");
   - decision → continue.
3. **Details rule (§7.3).**
4. **Reference (§6.8):**
   - above the maximum or interval too short → at least 🟠;
   - unknown drug or paediatric dosage → 🟠 « hors cadre : … »;
   - within the limits → `info` « conforme… » / « dans les limites… ».
5. **Downgrade to at most 🟠:**
   - low confidence → « confiance faible » ("low confidence");
   - second-check veto → « négation/hypothèse détectée » ("negation/hypothesis detected");
   - deciding sentence labelled UNCERTAIN.
6. **Otherwise ✅.**

When several outcomes apply, the worst wins: 🔴 > 🟠 > ✅. Every reason that applies is listed.

### 7.5 Omissions
A key in an authorized state (a decision, or an offer that was accepted and not later withdrawn) with no scribe action → `missing`, « manquant dans la note ».

### 7.6 False attribution
A Claim attributed **to the doctor here** ("comme vous disiez", "as you were saying"; "vous m'aviez dit", "you told me"), with no matching DOCTOR decision or offer in **this** consultation → banner « Fausse attribution : "…" — aucune phrase du médecin ne correspond » ("False attribution: '…' — no sentence from the doctor matches").

### 7.7 Advice from a third party
Mentions with `source = third_party` (Q4 "someone else"; EDS reported speech in Tier 2):
- they never authorize anything;
- they are accepted as history « rapporté par le patient » (§7.1);
- an action that comes from them carries the reason « conseil d'un tiers rapporté par le patient ».

The patient isn't accused of anything: the screen frames it as information, not fraud.

### 7.8 Confirmation
- **Spoken:** a new decision from the doctor, with details, becomes a new event.
- **Clicked (Tier 2):** « Confirmer » or « Remplacer… » is logged as a doctor action.
- **Generic** ("je confirme tout", "I confirm everything"): has no details, so 🟠 stays 🟠.

### 7.9 Live vs final
Live verdicts are provisional. « Fin de consultation »:
1. stops capture;
2. waits for pending tasks;
3. rebuilds the log;
4. runs a last scribe pass;
5. recomputes every verdict, omission and dose check;
6. marks them final.

« Signer » requires the final check and no 🔴, 🟠 or missing item left.

### 7.10 The demo scenario: reference results
**Situation:** an adult with a fever. Their mother works in a pharmacy, gives them ibuprofen, and told them to go back to work in 3 days. The doctor corrects both. **Nobody is cheating.**

**The script** (about 75 s; session date Saturday 10/10/2026):

| # | Voice | Line |
|---|---|---|
| 1 | DOCTOR | « Bonjour, installez-vous. Qu'est-ce qui vous amène aujourd'hui ? » ("Hello, have a seat. What brings you in today?") |
| 2 | PATIENT | « Bonjour docteur. Depuis trois jours j'ai de la fièvre, autour de 39, mal à la tête, des courbatures partout. Je suis vraiment épuisé. » ("For three days I've had a fever, around 39, a headache, aches everywhere. I'm exhausted.") (~8 s) |
| 3 | DOCTOR | « D'accord. Vous avez pris quelque chose pour la fièvre ? » ("OK. Have you taken anything for the fever?") |
| 4 | PATIENT | « Oui, ma mère travaille en pharmacie, elle me donne souvent de l'ibuprofène. Hier j'en ai pris **{N}**, des 400. Et elle m'a conseillé de reprendre le travail dans trois jours. » ("Yes, my mother works in a pharmacy, she often gives me ibuprofen. Yesterday I took {N} of the 400s. And she told me to go back to work in three days.") |
| 5 | DOCTOR | « Je vais vous examiner. Respirez fort par la bouche. » ("I'll examine you. Breathe deeply through your mouth.") |
| 6 | DOCTOR | « Bon, c'est une grippe. Non, l'ibuprofène on arrête, avec de la fièvre ce n'est pas une bonne idée. Vous allez prendre du paracétamol, trois fois mille milligrammes par jour, et vous reposer deux semaines. Je vous fais un arrêt. » ("It's the flu. No, stop the ibuprofen, it's not a good idea with a fever. You'll take paracetamol, three times a thousand milligrams a day, and rest for two weeks. I'll sign you off.") |
| 7 | PATIENT | « Deux semaines ? Je pensais reprendre lundi… » ("Two weeks? I was thinking of going back Monday…") |
| 8 | DOCTOR | « Non, deux semaines de repos, c'est important. Si la fièvre dure plus de cinq jours, on fera une prise de sang. » ("No, two weeks' rest, it's important. If the fever lasts more than five days, we'll do a blood test.") |

**{N}** is set after S8 so that N × 400 mg is above the ibuprofen maximum in the RCP for the product concerned. "Quatre" (four) is the placeholder.

**Bonus (Tier 3):** between lines 5 and 6, a phone plays a TV segment: « Contre la fièvre, l'ibuprofène 400, jusqu'à trois fois par jour. » ("For fever, ibuprofen 400, up to three times a day.") → « hors cadre : voix inconnue ».

**What Earshot does with each line:**
| # | Earshot |
|---|---|
| 1 | DOCTOR (phase A, strict threshold). Patient: waiting. |
| 2 | Provisional PATIENT (phase A, "not the doctor") → candidate A, a reply to the doctor, ≥ 6 s → commit → **« voix du patient apprise ✓ »**. History accepted. |
| 3 | DOCTOR (phase B). Mention of a drug, no event. |
| 4 | PATIENT. Q4 = *someone else*: Mentions `prescription:ibuprofene` {400 mg × N} and `sick_leave` {3 days}, source third_party. Q6: IntakeReport ibuprofen N × 400 mg in 24 h → **dose_alert**. |
| 5 | DOCTOR. No event. |
| 6 | DOCTOR. Events: `prescription:ibuprofene` **withdrawal**; `prescription:paracetamol` **decision** {1000 mg × 3, daily 3000}; `sick_leave` **decision** {14 days}. Conclusion « grippe » (flu) supported by the doctor. |
| 7 | PATIENT. Mention `sick_leave` {« lundi » → 2 days}, source self. |
| 8 | DOCTOR. `sick_leave` **decision** {14 days} again; `test_order:prise de sang` **conditional**. |

**Reference scribe output after line 8** (fixture; it reproduces realistic errors):
- history: fever 3 days 39 °C; aches; ibuprofen taken on the mother's advice;
- conclusion: flu;
- actions: ibuprofen 400 mg ×N/day; paracetamol 1 g ×3/day; « reprise du travail dans 3 jours » (back to work in 3 days) = sick_leave 3 days; blood test (prescribed).

**Expected verdicts:**
| Key | Status | Reasons / info |
|---|---|---|
| `prescription:ibuprofene` | 🔴 blocked | retiré par le médecin; conseil d'un tiers rapporté par le patient |
| `prescription:paracetamol` | ✅ authorized | info: conforme à la posologie usuelle (3 g/jour, RCP), if the RCP says so (S8) |
| `sick_leave` | 🔴 blocked | détail contredit le médecin (médecin : 14 jours) |
| `test_order:prise de sang` | 🟠 to_confirm | ordonnance conditionnelle |
| conclusion "grippe" | ✅ | — |
| history lines | ✅ | the ibuprofen line: « rapporté par le patient » |

**Alerts:** `dose_alert` (ibuprofen). No false attribution: the mother is a third party.

**After « Fin de consultation » (Tier 2):**
1. « Retirer » ibuprofen;
2. « Remplacer par la décision du médecin » on the sick note → 14 days ✅;
3. « Confirmer » the blood test as conditional;
4. « Signer » is now enabled.

**If the live scribe writes 14 days on its own,** the sick note is simply ✅. The demo works either way, and S5 measures what the scribe does.

## 8. The 3-minute demo
| Time | What happens |
|---|---|
| Before going on stage | The doctor's voice is loaded (recorded at the demo spot). Every status light is green. Patient: waiting. |
| 0:00 | Hook: *« Six millions de consultations ont déjà été écoutées par une IA. Elle sait ce qui a été dit. Elle ne sait pas qui avait le droit de le dire. »* ("Six million consultations have already been heard by an AI. It knows what was said. It doesn't know who had the right to say it.") |
| 0:15 | **Earshot OFF.** The actors perform §7.10 (lines 1–8). On screen: each sentence tagged **doctor (blue) / patient (green)**, and during line 2 *« voix du patient apprise »*. This is the core "it knows who's speaking" moment. The note fills up. *« Le médecin a 40 patients aujourd'hui. Il signe. »* ("The doctor has 40 patients today. He signs.") |
| 1:30 | **Earshot ON** (`E`). Ibuprofen 🔴 (withdrawn, third-party advice), sick note 🔴 (doctor said 14 days), paracetamol ✅ "conforme 3 g/jour", blood test 🟠, **dose alert** (click → RCP quote). *« Sa mère vient d'écrire l'ordonnance. »* ("His mother just wrote the prescription.") (Tier 2: click ibuprofen to play line 4, then the doctor's "non".) |
| 2:00 | (Tier 2) « Fin de consultation » → Retirer / Remplacer / Confirmer → « Signer ». (Tier 1 only: the presenter points out the corrections.) |
| 2:15 | Pitch (§13). |

**With 2 people:** the doctor-actor also presents and works the keyboard. The patient-actor plays the TV clip if the bonus is running.

**Fallbacks, in order:**
1. live microphone;
2. replay from a file;
3. offline mode (no internet);
4. video.

## 9. Edge cases
**Status:** ✅ handled by the design · 🧪 to test · ⚠️ known limit. IDs are kept from v2 for traceability.

### 9.1 Inside the domain (needs its own handling)
| # | Case | Expected | Status |
|---|---|---|---|
| A2 | Very short sentence (« oui ») | <1 s → UNCERTAIN; it carries no details and only ever *accepts* an offer (B26) | ✅ |
| A5 | Doctor's voice altered (a cold, turned away) | lower score → UNCERTAIN → 🟠 (safe) | 🧪 S1a |
| A14 | Drug name misheard | detail doesn't match → 🟠; the drug-name list may help (S3) | ✅/🧪 |
| A15 | Numbers in words, units | normalizer | 🧪 S8 |
| A18 | Relative dates (« lundi », « jusqu'à vendredi ») | our own code, counting from the session date | 🧪 S8 |
| A19 | Doctor's voice recorded somewhere other than the demo spot | always record at the demo spot, with the demo mic | ✅ |
| L1 | Patient's first answer shorter than 6 s | keep collecting over the following PATIENT turns until 6 s | ✅ |
| L2 | The doctor interjects during the first answer (« hmm ») | the one-voice check fails on that segment → not learned from; wait for the next one | ✅/🧪 |
| L3 | A doctor segment would join a candidate voice | strict τ_notD; S1a requires 0 occurrences | 🧪 S1a |
| L4 | The patient's voice is never learned (the patient barely speaks) | phase A continues: not-doctor = PATIENT (2-voice domain); the screen shows « voix du patient non apprise » ("patient's voice not learned") | ✅ |
| L5 | The patient's voice is polluted anyway | the two fingerprints look alike → UNCERTAIN → 🟠 (annoying, never dangerous) | ⚠️ |
| **L7** | **The TV (or another voice) speaks before the patient** | becomes candidate A, which never replies to the doctor. The patient is candidate B and replies to "qu'est-ce qui vous amène ?" → commit to B. A's rows retroactively become OTHER « voix non retenue comme patient » (grey), and their contributions drop out. | ✅ / 🧪 S1a (one take with the TV before line 2) |
| L8 | Two candidates tied after 3 doctor turns | Tier 1: most replies, then most seconds; Tier 2: the doctor picks with one click (▶ A ▶ B) | ✅ |
| L9 | The TV talks continuously while the patient barely speaks | the TV builds up seconds but no replies → never chosen while the patient replies at least once. If the patient never replies: no commit → non-doctor segments stay "provisional" → 🟠 on whatever depends on them | ✅ |
| B1 | Offer with all details + « oui » | ✅ | ✅ |
| B2 | Offer without details, the patient supplies them | 🟠 « détail dit par le patient » | ✅ |
| B3 | Doctor rephrases the request (« Vous voulez 15 jours, c'est ça ? ») | reformulation, no event | 🧪 S4 |
| B4 | Correction within the sentence (« 15… non, 10 jours ») | the latest value said wins | 🧪 S4 |
| B5/B6 | Withdrawal later / « pas d'arrêt » | 🔴 « retiré par le médecin » | ✅ |
| B7 | Mention in the history (« vous prenez du Doliprane ? ») | no event | 🧪 S4 |
| B8 | Renewal (« on continue le Kardegic ») | decision on `renewal:aspirine` | 🧪 S4 |
| B9 | Conditional (« si la fièvre dure… prise de sang ») | 🟠 | ✅ |
| B10 | « D'accord » to details the patient gave | 🟠 by design | ⚠️ |
| B11 | Joke (« un mois d'arrêt tant qu'on y est ! », "a month off while we're at it!") | should be a mention; the model may get it wrong | 🧪/⚠️ |
| B14 | Several actions in one sentence (line 6) | one event per key | ✅ |
| B15 | Scribe invents an action | 🔴 | ✅ |
| B16 | Brand name vs generic | BDPM + synonyms → same key | 🧪 S8 |
| B17 | Low confidence | 🟠 | ✅ |
| B18 | Generic confirmation | stays 🟠 | ✅ |
| B19 | A note line mixing several sources | one fact per line (S5) | 🧪 S5 |
| B22 | A pronoun refers to a drug named by the patient | drug detail « dit par le patient » → 🟠 | ✅ |
| B23 | Frequencies (« matin, midi et soir », « toutes les 8 heures ») | standard form | 🧪 S8 |
| B24 | Alternatives (« A ou B, on verra », "A or B, we'll see") | 🟠 | ✅/🧪 |
| B25 | Patient refuses an offer | 🔴 | ✅ |
| B26 | The « oui » to an offer is UNCERTAIN | it may accept: no details, and every detail comes from the doctor | ⚠️ |
| B27 | Omission | `missing` | ✅ |
| B28 | Planned recorded as done | 🟠 « statut différent » | 🧪 S5 |
| B29 | Patient reports an old prescription | no event; if the scribe turns it into an order → 🔴 | ✅ |
| B30 | Offer with no answer | 🟠 | ✅ |
| T1 | **Third-party advice** (« ma mère m'a conseillé… », line 4) | Mentions third_party; the action that comes from it → 🔴/🟠 + « conseil d'un tiers rapporté par le patient »; history « rapporté par le patient » | ✅ |
| T2 | « Mon ancien médecin me donnait… » ("My previous doctor used to give me…") | third party (another doctor) → same as T1, **not** a false attribution | ✅/🧪 S4 |
| T3 | « Vous m'aviez dit la dernière fois… » ("You told me last time…") | Claim attributed to the doctor, nothing matching in this session → false-attribution banner; the action → 🔴 « aucune phrase du médecin » | ✅ |
| T4 | « Reprendre dans trois jours » without saying what (work or medication?) | if Q1 can't decide → no event; scribe action → 🟠 | 🧪 S4 |
| D1 | « trois fois mille milligrammes par jour » | daily 3000 mg | ✅ |
| D2 | « 1 g trois fois par jour », « 1000 mg matin, midi et soir », « toutes les 8 heures », « 3 g par jour » | daily 3000 mg in every case | 🧪 S8 |
| D3 | Count × strength (« quatre, des 400 », « 5 Doliprane 1000 ») | count × the product's strength (BDPM) | 🧪 S8 |
| D4 | « Un comprimé » with no strength, product sold in several strengths | detail missing → 🟠 « détail non prononcé » | ✅ |
| D5 | Time window (« hier », "yesterday"; « depuis trois jours », "for three days"; « par jour », "a day") | 24 h window; for "for N days" with a daily amount, take the daily amount | 🧪 S8 |
| D6 | Prescription above the maximum / interval shorter than the minimum | 🟠 « dose au-dessus du maximum (RCP : X) » | ✅ |
| D7 | Patient reports an intake above the maximum (line 4) | `dose_alert` with the quote | ✅ |
| D8 | An RCP limit whose number isn't in the quote | rejected when loading → no comparison, info « référence indisponible » ("reference unavailable") | ✅ |
| D9 | Usual dose vs maximum (paracetamol: usual 3 g, max 4 g, to be read in S8) | ≤ usual → « conforme à la posologie usuelle »; ≤ max → « dans les limites »; > max → 🟠 | ✅ |

### 9.2 Leaving the domain, detectable → « hors cadre » (🟠 or alert)
| # | Case | Expected | Tier |
|---|---|---|---|
| A1 | Two people speaking at once | UNCERTAIN → 🟠 (segmentation in Tier 2) | 1/2 |
| A3 | Speaker change without a pause | Tier 1: the script avoids it; Tier 2: segmentation | 2 |
| A6/A7 | Accompanying person, interpreter | Tier 1: outside the domain (2 voices); Tier 3: « hors cadre : voix inconnue »; later: expand the domain (`todo.md`) | 3 |
| A10/A12/A20 | Phone on speaker, TV, background music | Tier 3: « hors cadre : voix inconnue » | 3 |
| A17 | Stage sound system | ask the organizers (S7); record the doctor's voice through the same chain; fallback: lapel mics | 1 |
| A8 | Patient silent | L4 | 1 |
| H1 | Doctor's voice not loaded / not recognised at the start | « hors cadre : médecin non enregistré / non reconnu » → stop | 1 |
| H2 | Action outside the 6 types | 🟠 « hors cadre : action non reconnue » | 1 |
| H3 | Drug not in the reference | 🟠 « hors cadre : médicament inconnu » (Tier 2: automatic retrieval, which can only give 🟠) | 1/2 |
| H4 | Paediatric or weight-based dosage | 🟠 « hors cadre : posologie pédiatrique » | 1 |
| L6 | The commit went wrong anyway (e.g. the TV happened to "reply" right after the doctor) | the real patient later scores low against the "patient" template → UNCERTAIN (Tier 1) / « hors cadre : voix inconnue » (Tier 3) → 🟠, and the doctor sees « voix du patient » next to the TV's rows. Never a false ✅. Roadmap: re-commit if another candidate keeps replying. | 1/3 |

### 9.3 Conditions of use (not detectable; stated)
| # | Condition | Why |
|---|---|---|
| A11 | No recording or AI clone of the doctor's voice is played | the voiceprint would match; no available detector handles replay through a loudspeaker; the doctor-worn mic is the roadmap fix |
| B12 | The doctor speaks only to the patient (no phone calls) | working out who the doctor is addressing is out of scope |
| B13 | One consultation = one session (start → sign) | anything said outside the session is ignored |
| B20 | The patient is responsible for what they report | Earshot checks who spoke, not whether it's true |
| B21 | The doctor is not complicit | out of scope |
| A13 | In-person, one room | teleconsultation audio is out of scope |

### 9.4 Scribe and demo
| # | Case | Expected | Status |
|---|---|---|---|
| C1 | The naive scribe makes no error on the new script | check in S5 which errors it really makes. If it makes none, change only the scribe prompt so it reflects market behaviour (e.g. a prompt that "lists every medication mentioned"); never the rules. Report it honestly. | 🧪 S5 (critical) |
| C2 | The scribe's output varies between runs | identity lives in the log; offline mode for the demo | ✅ |
| C3 | Trusting the scribe's own citations | never | ✅ |
| C4 | Verdict not ready when the switch goes ON | `pending` | ✅ |
| C5 | Jev struggles with French | routed to the LLM | 🧪 S4 |
| C6 | Real products can't be tested on stage | our own scribe, and we say so | ⚠️ |
| C7 | The scribe writes 14 days on its own | sick note ✅; the demo still works | ✅ |
| C8 | A service goes down | red light, banner, offline mode | ✅ |
| C9 | The scribe falls behind | after pauses, latest run wins, versioning | ✅ |
| C10 | The same drug written twice | 🟠 « action ambiguë » | ✅ |
| C11 | The final check takes too long | ≤ 10 s; rehearse | 🧪 |

## 10. Known limits (summary)
- **What Earshot does and doesn't check:** it checks who spoke, not whether it's true (B20). It doesn't catch a complicit doctor (B21).
- **Voice limits:**
  - a cloned or replayed doctor's voice gets through (A11);
  - overlapping speech is UNCERTAIN, not separated (A1);
  - two voices in the domain; a third voice is only *detected* (Tier 3);
  - accompanying people come later (`todo.md`).
- **Speech it can't fully interpret:**
  - who the doctor is talking to (B12);
  - jokes and subtle wording (B11, B3).
- **Safety comes first:** « d'accord » to the patient's details stays 🟠 (B10), as does an offer nobody answered (B30). A short « oui » labelled UNCERTAIN can still accept an offer (B26).
- **Dosage checks:**
  - adults only;
  - drugs in the table only (Tier 2: automatic retrieval, which can only give 🟠);
  - no cumulative dose across the patient's own intake and a prescription;
  - no drug interactions.

  The limits come from the RCP, extracted by an LLM and then verified (the numbers must appear in the quote, plus a human read-through).
- **Scope of the demo:**
  - French only, one room, room microphone;
  - our own scribe, not a real product (C6);
  - **not a medical device.**
- **Biometric data (GDPR Art. 9):**
  - the doctor's voiceprint is stored on the laptop with the doctor's consent;
  - the patient's voiceprint lives only in memory and is deleted when the session is reset.

  In production, this needs explicit consent and storage on the device itself.
- **Cloud and logs:**
  - transcripts go to cloud services; production would need HDS-certified hosting (Hébergeur de Données de Santé, France's certification for health-data hosting);
  - Jev retains no data only on its enterprise plans;
  - the audit trail is not a signature.

## 11. Decisions and open questions
**Decided:**
- **From earlier versions:**
  - approach C, live checking;
  - 2 developers, French;
  - Jev where it fits;
  - code written at the event;
  - tiers;
  - action log, offers that need acceptance, final check;
  - no doctor-worn mic.
- **New in v3:**
  - operating domain;
  - doctor's voice recorded once, patient's voice learned;
  - drug and dose reference, with standard dose quantities;
  - third-party advice;
  - 8-line script.

**Open (settled by the tests):**
1. Is code written before the event allowed? (S7)
2. Which LLM plays the naive scribe? (S5)
3. Jev or LLM for each question, and the τ_conf thresholds. (S4)
4. Which embedding model; τ_D_solo, τ_notD, τ_D, τ_P, m, τ_cons; seconds needed to learn the patient's voice. (S1a)
5. Per-duration thresholds. (S1b)
6. The TV tag. (S6)
7. Drug-name hints. (S3)
8. The RCP limits, and N in line 4. (S8)

## 12. Before the event: throwaway tests (about 17 h; S7 then S1a first)
**All test code is deleted.** Kept: recordings, `reference/drug_limits.json` with its quotes, cached RCP texts, and results in `earshot/docs/test-results.md`.

| # | Question | How | Pass if | Owner | Time |
|---|---|---|---|---|---|
| S7 | Practical details | Ask the organizers: is code written before the event allowed, stage microphones (A17), wifi, length of the demo slot | – | either | – |
| **S1a** | **Does it know exactly who's speaking? Does it learn the patient's voice?** | With the two actors, on the demo Mac and microphone: record the doctor's voice once (2–3 × 20–30 s). Record the §7.10 script 5 times, plus 3 minutes of free conversation, **plus 1 take with a TV clip played before line 2 (L7)**. Label everything by hand. Compare ECAPA and WeSpeaker. Learning the patient's voice from the first answer: compare 4, 6 and 8 s with the dedicated clips. Search τ_D_solo, τ_notD, τ_D, τ_P, m and τ_same. Check that the commit picks the patient in the TV take. | **100% correct** on the script; **0** patient segments labelled DOCTOR; **0** doctor segments in a candidate voice; commit correct in the TV take; ≤ 10% UNCERTAIN in free conversation. Record the model, the thresholds and the learning duration. If it fails: fix recording and mic placement first; lapel mics are the last resort. | Dev A | 2.5 h |
| S2 | Speed | From end of sentence to label + text on the Mac (CPU and MPS, the Mac's GPU) | ≤ 2 s for 9 sentences out of 10 | Dev A | 1 h |
| S3 | Voxtral | 20 French sentences (drugs, doses), with and without drug-name hints; check the endpoint, model, word timestamps and cost | drugs and numbers correct; timestamps present (otherwise use the Whisper fallback) | Dev A | 1.5 h |
| S4 | The questions | ≥ 10 French sentences for each kind of statement; accept/refuse; Q4 (doctor / someone else / nobody); Q6. Cover B3, B4, B7, B8, B11, B24, B29, T2, T3, T4. Adversarial set. Compare Jev, the LLM, Jev + EDS, and the two together. | **0 unsafe ✅**; record the 🟠 rate, τ_conf, and the routing | Dev B | 3 h |
| S5 | Naive scribe | Typical prompt with neutral labels on the §7.10 script, 10 runs: which errors does it make (ibuprofen as a prescription, sick note 3 days, blood test written as done)? Stability over 5 runs; C7; B19. | errors documented; prompt fixed (C1); identity stable through the log | Dev B | 1.5 h |
| **S8** | **Normalizer + drug reference** | ~30 test phrases (doses, frequencies, durations, dates, brands, « des 400 », « trois fois mille milligrammes »): our own code vs text2num, EDS and dateparser. **Download the BDPM files; get the RCP dosage sections** for the demo drugs (check the method); extract `DrugLimits` with an LLM, then check that every number is in its quote and read them by hand; set N in line 4 above the ibuprofen maximum. | each library's role decided; `reference/drug_limits.json` checked; N set | Dev B | 2.5 h |
| S1b | Hard conditions (Tiers 2–3) | Fast turn-taking, overlaps, short interjections, TV, replay, clone (with consent), sound system; set of other voices; variants A–E | per-duration thresholds; replay/clone documented | Dev A | 4 h |
| S6 | TV tag (optional) | YAMNet on TV audio vs live speech | threshold, or drop it | Dev A | 1 h |

## 13. Startup story (for the pitch)
- **Buyers:**
  - scribe vendors, as an SDK (Nabla, Doctolib, Tandem);
  - hospitals;
  - insurers: Assurance Maladie, top-up health insurers (mutuelles), medical liability insurers (MACSF, Relyens).
- **Pricing:** per consultation or per doctor seat.
- **Why independent:** a scribe vendor can't certify itself, and insurers want a neutral check.
- **Why existing tools fall short:**
  - they identify speakers by device (Granola, Zoom) or by the text (AssemblyAI);
  - their evidence links are for reading, not enforcing (HealthScribe, Abridge);
  - **Earshot ties authority to the voice, checks doses against the official reference, and enforces both.**
- **Two kinds of problem it solves:**
  - honest confusion, the common case: advice from a family member, a patient asking to go back to work;
  - deliberate manipulation, the rare case.

  Both lead to the same mistake: something becomes a prescription without the doctor deciding it.
- **Why now:**
  - scribes now draft actions, not just notes;
  - regulators treat scribes as medical devices; the operating domain is our MDR intended-use statement;
  - AI Act obligations in August 2028;
  - audits show omissions and "options recorded as prescriptions".
- **Expansion:** a "speaker of record" for every AI that listens.
- **Roadmap:**
  - anti-spoofing and a doctor-worn mic;
  - accompanying people (expanding the domain);
  - teleconsultation;
  - cumulative doses and drug interactions;
  - HDS-certified hosting.

## 14. Build plan: 36 h, 2 developers
Details in `earshot/docs/plan.md`.

| Hours | Dev A: sound and screen | Dev B: brain |
|---|---|---|
| 0–2 | **Both:** repo, data formats (§5.1), the §7.10 fixture, stubs | |
| 2–8 | Tier 1: capture, sentence cutter, doctor enrollment (one-off), patient learning, phases A/B | Tier 1: normalizer + standard dose quantities, drugs + reference + dose checks, action log, rules, matcher (tests) |
| 8–14 | Tier 1: screen (transcript, voice state, note, badges, alerts, switch) | Tier 1: naive scribe, Q1–Q6, cache/offline |
| 14–18 | **Tier 1 integration**, replay of S1a and the demo; **Tier 1 end-to-end by hour 18** | integration + end-to-end reference test |
| 18–24 | Tier 2: segmentation, per-duration thresholds, playback, final check / Signer, doctor buttons | Tier 2: final check, omissions, EDS, audit trail, automatic retrieval for unknown drugs |
| 24–26 | Tier 3 (if stable): third voice, AS-norm, TV tag, TV clip | Tier 3: TV line in the reference test |
| 26–30 | **Both:** 10 rehearsals, offline cache, video | |
| 30–32 | fixes only | fixes only |
| **32** | **code frozen** | |
| 32–36 | **Both:** pitch, checklist | |

## 15. Test plan
1. **Rules, log, third-party advice (automated):** one test per in-domain case (§9.1), with the kinds of statement and the events given directly.
2. **Normalizer and dose quantities (automated):** D1–D5, A15, A18, B23, and the S8 table.
3. **Reference (automated):** the loader rejects a limit whose number isn't in its quote (D8); the checks D6, D7, D9.
4. **Voice (automated, on the S1a recordings):** phases A/B, learning, 0 patients labelled DOCTOR, 0 doctor segments learned as the patient, noise added (−6 dB, SNR 10 dB).
5. **Matcher (automated):** C10, omissions, `hors cadre`.
6. **Questions (model):** re-run the S4 confusion set; **any unsafe ✅ blocks the change**.
7. **End to end:** offline, with the demo recording, reproduce §7.10 **exactly**, including the alerts and, in Tier 2, the final check.
8. **Checklist before going on stage:**
   - mic level;
   - doctor's voice loaded (recorded at the demo spot);
   - lights green;
   - offline mode tested;
   - TV clip (bonus);
   - video open.

## 16. The hardest technical problems
*With the domain and Tier 1 (two known voices, the doctor recorded on site, scripted turns), problem 1 is in its easiest form. The hard version below applies to Tiers 2–3 and to a real product.*

1. **Who is speaking, in real conditions.**
   - Short sentences, room echo, recording conditions, overlap, sound system.
   - Learning the patient's voice adds one specific risk: a doctor segment joining a candidate voice (L3).
   - Mitigations:
     - record the doctor at the demo spot;
     - a strict τ_notD;
     - a one-voice check;
     - the doctor's voiceprint is never updated;
     - S1a.
2. **Linking the scribe's note to who said what.** Mitigations:
   - the log carries identity;
   - details come from the doctor's own words;
   - standard dose quantities;
   - everything tested on fixtures.
3. **Classifying statements in French (model choice).**
   - The risky cases: offer, alternatives, reformulation, jokes, third party vs "the doctor here".
   - Mitigations:
     - offers need acceptance;
     - alternatives never authorize;
     - EDS;
     - zero unsafe ✅ in S4;
     - work on the wording first.
4. **Reliable drug reference data.**
   - An LLM extracts the limits from the RCP, then they are verified: the number must be in the quote, plus a human read-through.
   - Comparisons are on numbers only, never on "meaning".
5. **The live pipeline.** After pauses, the latest run wins, one event loop, versioned snapshots.
6. **A believable "victim" scribe.** A typical prompt with neutral labels, with its errors measured in S5.

**Not hard:** the screen, the audit trail, the cache, the rule engine, the reference lookup.

## 17. Industry and research review (v2, unchanged)

### 17.1 How others attribute speakers
| Company | Method | For Earshot |
|---|---|---|
| Granola | "Me" (microphone) vs "Them" (system audio); names from the meeting platform; inference from context | needs one device per person; "cannot distinguish the individuals" sharing a device |
| Zoom AI Companion | the signed-in account | credits that user with podcasts, other people… |
| Teams Rooms + Copilot | voice profiles of invited people | the closest, but needs invitations and certified microphones |
| AWS HealthScribe | 2 channels or roles; `EvidenceLinks` | US English; "probabilistic" links |
| Abridge | "Linked Evidence" | review, not enforcement |
| Nabla | doctor/patient labels; advice to say names out loud | roles probably come from the words (our inference) |
| Dragon Copilot | multilingual (French) mode | "don't indicate who is speaking" |
| AssemblyAI | live diarization, `PENDING` under 1 s; names inferred from text | the text can be manipulated |
| Speechmatics | identification against enrolled speakers | no confidence score or languages documented |
| pyannoteAI | voiceprints, `null` if no match | we adopted its enrollment practices |
| Picovoice Eagle | on-device enrolled scores | distant microphone not tested |
| Wispr Flow | 700 ms end-to-end target | timing benchmark |

### 17.2 What we took
- **Enrollment:** several templates, an explicit "unknown" outcome (Speechmatics, pyannoteAI, Teams).
- **Provisional labels** (AssemblyAI).
- **Audio playback** (Abridge).
- **Evidence for every action** (HealthScribe, MEDIQA-OE).
- **List-then-check for omissions.**
- **The audit's failure clusters.**
- **"Models read, code decides" plus spotlighting** (prompt-injection design patterns).
- **Send only low-confidence cases to the LLM** (Posos).

### 17.3 What we rejected
- **Doctor-worn microphone:** declined by the user; on the roadmap.
- **Streaming or end-to-end diarization** (Sortformer, Nemotron 3, DiariZen, DiCoW, SpeakerLM): weak in French, offline only, GPU only, or not commercially licensed, and none of them identifies the doctor.
- **Speaker labels inferred from text.**
- **NeMo text normalization.**
- **Fine-tuned dialogue-act models and whole-transcript order extractors** (~60% F1).
- **Anti-spoofing detectors** (no replay through a loudspeaker).
- **Two models must agree:** test only.
- **Reading a random phrase out loud:** roadmap.
- **Comparing doses by semantic similarity** (v3): rejected in favour of standard numeric quantities (§6.8).

## 18. Sources
**Products:**
- Doctolib: https://about.doctolib.fr/news/intelligence-artificielle-doctolib-lance-lassistant-de-consultation/
- Nabla: https://techcrunch.com/2023/03/14/nabla-a-french-digital-health-startup-launches-copilot-using-gpt-3-to-turn-patient-conversations-into-actionable-items/
- Abridge: https://www.abridge.com/blog/orders-real-time-clinical-documentation
- HealthScribe: https://docs.aws.amazon.com/ai/responsible-ai/aws-healthscribe/overview.html
- Granola: https://docs.granola.ai/help-center/taking-notes/speaker-attribution
- Wispr: https://wisprflow.ai/research/technical-challenges
- Teams: https://learn.microsoft.com/en-us/microsoftteams/rooms/voice-recognition
- Zoom: https://lthelp.yorku.ca/introduction-to-zoom-ai-companion
- Dragon: https://support.microsoft.com/en-us/dragon-copilot/physicians/multilingual-conversations
- AssemblyAI: https://assemblyai.com/docs/streaming/streaming-diarization
- Speechmatics: https://docs.speechmatics.com/speech-to-text/realtime/realtime-speaker-identification
- pyannoteAI: https://docs.pyannote.ai/tutorials/identification-with-voiceprints
- Picovoice: https://picovoice.ai/docs/quick-start/eagle-python/
- Voxtral: https://mistral.ai/news/voxtral-transcribe-2

**Voice:**
- segmentation-3.0: https://huggingface.co/pyannote/segmentation-3.0
- ERes2NetV2: https://arxiv.org/html/2406.02167v1
- ReDimNet: https://github.com/idrnd/redimnet
- WeSpeaker ResNet34: https://huggingface.co/pyannote/wespeaker-voxceleb-resnet34-LM
- ASVspoof 5: https://arxiv.org/html/2601.03944v1
- ReplayDF: https://arxiv.org/html/2505.14862v2
- YAMNet: https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv

**Text and drugs:**
- Audit: https://arxiv.org/abs/2608.31017
- Omissions: https://arxiv.org/abs/2608.31016
- MEDIQA-OE: https://arxiv.org/abs/2510.26974
- Posos: https://arxiv.org/html/2506.19525v1
- HAS (French National Authority for Health), posology: https://has-sante.fr/jcms/p_3555137/fr/structuration-de-la-posologie-des-medicaments
- FHIR EventTiming: https://hl7.org/fhir/R4/valueset-event-timing.html
- PxSLU: https://arxiv.org/pdf/2207.08292
- EDS-NLP: https://aphp.github.io/edsnlp/latest/pipes/
- BDPM: https://base-donnees-publique.medicaments.gouv.fr/telechargement
- CaMeL: https://arxiv.org/abs/2503.18813
- Design patterns: https://arxiv.org/abs/2506.08837
- Spotlighting: https://arxiv.org/abs/2403.14720
- Noise: https://arxiv.org/abs/2606.05909
- Assurance Maladie: https://www.ameli.fr/assure/actualites/en-2025-l-assurance-maladie-detecte-et-stoppe-723-millions-d-euros-de-fraudes
- MDR/Tandem: https://tandemhealth.ai/resources/news/tandem-s-ai-scribe-is-now-mdr-class-iia-certified
