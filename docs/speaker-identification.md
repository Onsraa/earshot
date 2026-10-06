# How Earshot recognises who is speaking

## The idea in one paragraph
Every voice has a timbre that comes from the body: the length and shape of the vocal tract, the vocal cords, the usual pitch and resonance. A neural network (ECAPA-TDNN) turns any clip of speech into **192 numbers describing that timbre, not the words**. This is a *voice fingerprint*.

- **The doctor** records their voice **once**, at setup.
- **The patient never records anything.** Earshot learns their voice automatically, by spotting **which voice answers the doctor**.

**Earshot never decides who is speaking from the words.** A patient who *talks like* a doctor still has the patient's voice.

## Why this works with no friction
Only the doctor's voice can authorize an action, so only the doctor needs a voiceprint recorded in advance. The patient's voice never grants authority. If Earshot gets it wrong, the result can be a 🟠 or an alert, but never a false ✅.

The setting is fixed (spec §2.2): one doctor, one adult patient, one room, one microphone. That scope is what lets Earshot learn the patient's voice without asking anything.

## Step by step

```
 ONCE (setup, at the demo spot, same microphone)
   doctor reads 2–3 texts (20–30 s each) → 2–3 doctor fingerprints, saved on the laptop

 EACH CONSULTATION
   start → doctor fingerprints loaded · patient: waiting
   microphone → sentence cutter (pause ≥ 0.6 s) → sentence audio
                 ├→ fingerprint of the sentence → compared with the doctor (and the patient once learned)
                 └→ transcription (Voxtral) → the words, shown next to the label
```

1. **Recording the doctor (once).**
   - The doctor reads 2–3 short texts, at the demo spot, through the demo microphone.
   - Each reading must contain at least 15 s of speech and **only one voice**. Otherwise it is rejected and recorded again.
   - The fingerprints are saved on the laptop and loaded automatically every time.
   - **They are never modified during a consultation.**
2. **Cutting into sentences.** A voice-activity detector (Silero VAD) cuts after 0.6 s of silence.
3. **Phase A: before Earshot knows the patient's voice.** Earshot can only ask "is this the doctor?":
   - **DOCTOR** if the match with the doctor is strong (strict threshold τ_D_solo);
   - **"not the doctor"** if it is clearly weak (τ_notD). In a two-person consultation, that means the **patient**, shown in light green until confirmed;
   - **UNCERTAIN** in between, or if the sentence is shorter than 1 s.
4. **Candidate voices.** Every "not the doctor" segment is grouped by voice: candidate A, B…
   - **Grouping:** a segment joins a candidate if its fingerprint is close enough to that candidate's average (τ_same). Otherwise it starts a new one.
   - **Two counts per candidate:** how many seconds it has spoken, and how many times it has **replied to the doctor**. A reply is a turn that starts within 2 s after the doctor stops talking.
5. **Choosing the patient (the commit).**
   - **Rule:** the patient is the candidate that has spoken **≥ 6 s** and **replied to the doctor at least once**. If several qualify, the one with the most replies wins, then the one with the most seconds.
   - **When:** in practice this happens during the answer to « Qu'est-ce qui vous amène ? » ("What brings you here?").
   - **On screen:** a progress bar, then **« voix du patient apprise ✓ »** ("patient's voice learned").
   - **What it changes:** the chosen voice becomes the patient. Any other candidate (a TV, a voice in the corridor) becomes **OTHER** after the fact, its rows turn grey, and what it said stops counting.
6. **Phase B: after the commit.** Earshot compares each sentence with **both** voices:
   - **DOCTOR** if the doctor score is high enough **and** clearly above the patient score (margin m);
   - **PATIENT** in the same way, the other way round;
   - **UNCERTAIN** otherwise, or under 1 s.
   - The patient's voiceprint improves as they speak: a clear patient segment of 3 s or more is added, up to 5 fingerprints. **The doctor's fingerprints never change.**

## What if the TV (or someone else) speaks before the patient?
Earshot doesn't commit to "the first voice that isn't the doctor". It commits to **the voice that answers the doctor**:

| Moment | Who | What Earshot does |
|---|---|---|
| 0:02 | TV: « Contre la fièvre, l'ibuprofène 400… » ("For fever, ibuprofen 400…") | not the doctor → candidate **A**: 4 s, **0 replies** (the doctor hasn't spoken yet) |
| 0:06 | Doctor: « Bonjour… Qu'est-ce qui vous amène ? » | DOCTOR |
| 0:09 | Patient: « Depuis trois jours j'ai de la fièvre… » (8 s, starts 1 s after the doctor) | not the doctor, a different voice from A → candidate **B**: 8 s, **1 reply** → **commit to B** |
| — | — | the TV's rows (A) become **OTHER, "voix non retenue comme patient"** ("voice not kept as patient"), greyed out, and their contribution to the note is removed |

**Why it works:** a TV talks on its own schedule. A patient answers the doctor. This uses **when** people speak, not **what** they say, and it is only used to tell *patient* from *other*. It never gives anyone doctor authority.

**If it still goes wrong** (the TV happens to "reply" right after the doctor): the real patient then matches the "patient" voiceprint poorly, so their sentences come out UNCERTAIN, or "unknown voice" in Tier 3. The result is 🟠, never a false ✅. In Tier 2, if two candidates are tied, the doctor picks with one click: « Quelle voix est le patient ? ▶ A ▶ B » ("Which voice is the patient?").

## Example on the demo script (illustrative numbers; real thresholds come from S1a)
Assume τ_D_solo = 0.60, τ_notD = 0.30, τ_D = 0.55, τ_P = 0.50, m = 0.20.

| # | Sentence | s_D | s_P | Result |
|---|---|---|---|---|
| 1 | « Bonjour, installez-vous. Qu'est-ce qui vous amène ? » | 0.74 | – | phase A: 0.74 ≥ 0.60 → **DOCTOR** |
| 2 | « Depuis trois jours j'ai de la fièvre… » (8 s, reply) | 0.15 | – | ≤ 0.30 → not the doctor → candidate A, 8 s, 1 reply → **commit** → **PATIENT** |
| 4 | « Oui, ma mère travaille en pharmacie… » | 0.18 | 0.69 | phase B → **PATIENT** |
| 6 | « Bon, c'est une grippe. Non, l'ibuprofène on arrête… » | 0.71 | 0.21 | phase B → **DOCTOR** |
| – | « Oui. » (0.4 s) | – | – | < 1 s → **UNCERTAIN** |

## Why the thresholds lean one way
The costly mistake is **calling the patient the doctor**, because that would give them authority. The second-worst is **mixing the doctor's voice into the patient's fingerprints**. So τ_D_solo, τ_notD, τ_D and m are tuned in S1a for **zero** occurrences of either. The price is that a few real doctor sentences become UNCERTAIN. The doctor then confirms those actions with a word or a click.

## Why it will hold up in the demo (Tier 1)
- **Two known voices.** The doctor is recorded on site with the same microphone, and the patient is learned from a natural 8 s answer.
- **A scripted dialogue.** Turns are separated by pauses, and each line lasts at least 1.5 s.
- **A clear test.** S1a must reach 100% on the script, including a run where the TV speaks before the patient.
- **Last resort:** one lapel microphone per person. The louder channel then tells who is speaking.

## Later
- **Tier 2:** a second model (segmentation-3.0) handles speaker changes with no pause and overlapping voices. Thresholds depend on segment length.
- **Tier 3:** a **new** unknown voice *after* the commit becomes OTHER, « hors cadre : voix inconnue » ("outside scope: unknown voice"). Scores are normalized (AS-norm) against a set of other voices, and an optional "TV" tag can only downgrade a label.
- **Several patients or accompanying persons:** widen the scope according to the appointment type (`todo.md`).

## What it can't do (yet)
- **A recording or AI clone of the doctor's voice** has the doctor's timbre, so it gets through. A microphone worn by the doctor is on the roadmap.
- **Overlapping voices** are marked UNCERTAIN, not separated.
- **French only, in one room.** Teleconsultation is out of scope.
