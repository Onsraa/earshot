# Context

## The event
- **ESSECKATHON "Secure Horizons":** ESSEC Business School, Cergy campus, **10–11 October 2026**, 36 hours non-stop, about 150 participants. Theme: *"design, attack and secure complex agentic architectures"*. €15,000 in prizes and infrastructure credits. Three unpublished use cases were announced.
- **Organisers:** KRYPTOSPHERE® ESSEC, Utopia, ESSEC Metalab Institute.
- **Partners:** AWS, GitGuardian, Artefact, KPMG, Bpifrance, Avalanche Team1, ESSEC Alumni.
- **Tracks:**
  1. **Guardians of Value:** financial systems, transactions, digital assets. Jury: Team1 (Avalanche), KPMG, KRYPTOSPHERE.
  2. **Defenders Augmented:** AI for security, and security of AI. Jury: GitGuardian, ESSEC MetaLab, KPMG.
  3. **Uncharted Frontiers:** new, complex security challenges beyond the standard categories. Jury: **Bpifrance, ESSEC Alumni, UTOPIA**.
- **Not known yet:** team size limits, judging criteria, and whether code may be written before the event. Ask the organisers (Phase 0, S7).

## Our choice: Track 3
- **What the user wants:** real novelty, and a short demo with marketing impact.
- **The jury** is investors and business people, so the pitch and the startup story count as much as the code.
- **The priority, set by the user:** a working, clean demo. Two people talk, and Earshot knows exactly who is speaking. The TV attack is a bonus.

## How Earshot was chosen
Several rounds of research (2026-10-05 and 2026-10-06) produced about 35 Track 3 ideas. Each was checked for novelty against papers, products and startups. The shortlist:
- **Earshot:** AI scribes can't tell who has the authority to speak. Novelty about 4/5. French health and fraud story. Chosen.
- **Mosaic:** finds a crime split across harmless gigs that AI agents post for humans. Novelty 5/5, but there are few buyers today.
- **Verbatim:** checks that AI interpreters speaking in your voice haven't been manipulated.
- **Soul Alarm:** fake "canary" memories that reveal when an AI assistant's memory is stolen.
- **Rubber Stamp:** tests whether the humans approving AI actions really pay attention.
- **Quorum:** finds fake "citizens" in public consultations.

The full list of ideas, including those dropped and why, is in `../../docs/ideas.md`.

## Why Earshot (summary; evidence in spec §3)
- **Scribes are widespread in France:** Doctolib's assistant has been used in more than 6 million consultations, and Nabla has thousands of French doctors.
- **Scribes now draft actions,** not just notes.
- **An audit of 3 commercial scribes** found a verified failure in 31.3% of notes. Recurring patterns: options written up as issued prescriptions, withdrawn items recorded as done, sick-note plans left out.
- **No product ties authority to the voice in one shared room.** Existing tools identify speakers by device (Granola, Zoom) or guess roles from the words (AssemblyAI, Granola), and both break in a shared consultation room.
- **France's health insurer** (Assurance Maladie) stopped €49M of fake sick-leave fraud in 2025, and regulators now treat scribes as medical devices.

## Team and constraints
- **2 developers.** Dev A does sound and the screen; Dev B does the "brain".
- **Demo:** in French, on one Mac laptop with a room microphone, plus cloud services (Voxtral, Jev, one LLM).
- **Code timing:** all product code is written during the 36 hours. Code for this week's tests is thrown away; only the recordings and the results are kept.
- **Jev** (a fast, cheap AI model that returns typed decisions with confidence) is used where it fits. An LLM is the fallback.
- **Demo data is invented.** No real patient data is used.
