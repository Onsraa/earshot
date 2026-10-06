# Earshot

**AI scribes record what was said. Earshot checks who had the right to say it, and whether the dose is right.**

Earshot sits between an AI medical scribe and the medical record:
- It recognises **who is speaking by their voice**. The doctor records once; the patient's voice is learned automatically from their first answer.
- It checks every action the scribe drafts:
  - ✅ authorized
  - 🟠 the doctor must confirm it
  - 🔴 blocked: not said and meant in the doctor's own voice
- It checks doses against the official drug information: "3 fois 1000 mg" ↔ "3 g par jour".
- It alerts the doctor when the patient reports taking too much of a drug.
- It works inside a defined **operating domain** (one doctor, one adult patient, one room). Outside that domain it never guesses: it hands control back to the doctor.

It is a hackathon project for **ESSECKATHON "Secure Horizons"** (ESSEC Cergy, 10–11 October 2026), **Track 3, "Uncharted Frontiers"**.

Pitch line: *« Sa mère vient d'écrire l'ordonnance. »* ("His mother just wrote the prescription.")

## Status
- **2026-10-06:** design v3 agreed, implementation plan written.
- **This week:** throwaway tests (Phase 0 of the plan), with results recorded.
  - Done: drug reference (S8).
  - Prepared: the voice test (S1a; waiting for the actors) and the API tests (S3–S5; waiting for keys).
- **10–11 October:** build on site, Tier 1 first.

## Folder map
| Path | What it is |
|---|---|
| `docs/context.md` | The hackathon, the jury, why this idea, the team and the constraints |
| `docs/spec.md` | **The design (v3)**: operating domain, architecture, rules, drug reference, demo script, edge cases, limits, tests, sources |
| `docs/speaker-identification.md` | How Earshot recognises the doctor and learns the patient's voice, including when the TV speaks first |
| `docs/plan.md` | **Implementation plan**: Phase 0 this week, then 22 tasks by tier for the 36 hours |
| `docs/architecture.md` | Components, concurrency, state machines, REST/WebSocket interface, snapshot format, config, timing, failure handling, data boundaries |
| `docs/models.md` | Every model: role, verified version and API, fallbacks, models rejected |
| `docs/prompts.md` | Prompt spec v1: spotlighting, the single batched Jev call per sentence, LLM fallback, scribe, RCP extraction, evaluation |
| `docs/infra.md` | Python 3.12 environment, pinned dependencies, keys, downloads, network, costs, hardware, day-of runbook |
| `docs/s1a-recording-guide.md` | How to record and analyse the two-actor voice test |
| `docs/organizer-email.md` | Questions for the organisers (S7) |
| `docs/test-results.md` | Phase 0 results: thresholds, rates, model choices, drug limits |
| `docs/todo.md` | Later: several patients or accompanying persons, and more |

The idea tracker that led to Earshot is `../docs/ideas.md`.

## Read in this order
1. `docs/context.md`
2. `docs/spec.md`: §1–2, §7.10 (the demo scenario), §6.4 and §6.8
3. `docs/speaker-identification.md`
4. `docs/architecture.md`, `docs/models.md`, `docs/prompts.md`, `docs/infra.md`
5. `docs/plan.md`

## Key decisions
**Scope and priority**
- **A working, clean demo.**
  - **Tier 1:** two voices, Earshot knows exactly who is speaking, blocks what the doctor didn't authorize, and checks doses.
  - **Tier 2:** robustness and polish.
  - **Tier 3:** bonus, the TV.
- **Operating domain:** one doctor, one adult patient, one room, one microphone, French, 6 action types, drugs in the reference.
  - **Inside the domain:** exact behaviour.
  - **Detected departures:** marked « hors cadre » ("out of scope") and handed to the doctor.
  - **Departures it can't detect:** stated as conditions of use.

**Who is speaking**
- **The voice decides, never the words.** Models only read meaning; code decides authority.
- **The doctor's voice is recorded once.** The patient's voice is learned through candidate voices. Earshot commits to the voice that replies to the doctor, so a TV heard first is set aside.

**What gets checked**
- **Doses:** "find by meaning, decide on numbers." The drug reference (BDPM plus the dosage section of each drug's official summary, the RCP) is turned into a limits table with quotes, and code compares standard quantities.
- **Advice from a third party** ("ma mère m'a conseillé…", "my mother told me to…") is recorded as history and never authorizes anything.
- **The doctor's decisions** go into an append-only log, and the note is checked against it, which also catches omissions.
- **Offers need the patient's acceptance.** Alternatives never authorize anything on their own.
- **An end-of-consultation check runs before signing.**

**Practical constraints**
- French demo.
- 2 developers.
- All product code written during the event.
- Jev where it fits, with an LLM as fallback.

**Not adopted:** a microphone worn by the doctor. It is on the roadmap.
