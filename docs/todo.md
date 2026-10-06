# To do later (not for the hackathon)

## 1. Several patients, or someone accompanying the patient
**Today:** one person besides the doctor can be enrolled. Anyone else is OTHER, and what they say is excluded (spec A6, A7). That breaks common real cases:
- **Paediatrics:** a parent describes the child's symptoms and agrees to the treatment.
- **Elderly or dependent patients:** a carer or relative speaks for them.
- **Interpreters,** and patients who are hard of hearing.
- **Couple or family consultations:** several patients in one visit.

**Ideas to research:**
1. **Enroll N people, each with a role.** Roles: *patient*, *accompanying person* (parent, carer), *interpreter*, *second patient*. Each role gets explicit permissions:

   | Role | Can report history | Can accept an offer | Can authorize an action |
   |---|---|---|---|
   | Patient (adult) | yes | yes | never (doctor only) |
   | Parent / legal guardian of a minor | yes (for the child) | yes (parental authority) | never |
   | Carer | yes, flagged « rapporté par l'accompagnant » ("reported by the accompanying person") | no, unless legally appointed | never |
   | Interpreter | yes, flagged « traduit » ("translated"), linked to the patient | no | never |

2. **Voices that are not enrolled.** Group the unknown voices live into « Inconnu 1, 2… » (unknown 1, 2…). The doctor assigns a role with one click, and that person's first sentences become their reference. Streaming separation models can sort up to 4 speakers; Streaming Sortformer is one to evaluate.
3. **Quick enrollment** during the identity check: "*Et vous êtes… ?*" ("And you are…?") records a reference for the accompanying person.
4. **Attach every statement to a patient.** With several patients, every action key gets a patient id (`patient_id:prescription:paracetamol`), and Q1 has to work out who the action is for.
5. **How others do it** (from the v2 research):
   - Speechmatics allows up to 50 enrolled identifiers.
   - pyannoteAI voiceprints return `null` when nothing matches.
   - Teams Rooms matches only against the people invited to the meeting.

   Check how each handles enrolling several people, and how they fail.
6. **Legal questions to check:**
   - Who may accept on behalf of a minor or of an adult under legal protection (*tutelle*, *curatelle*)?
   - Consent to record voiceprints for everyone in the room (GDPR, Article 9).
7. **Edge cases to add:**
   - a parent and the child both talking;
   - two accompanying people with similar voices;
   - an interpreter and a patient speaking the same sentence in two languages;
   - the role assigned late in the consultation.

8. **Widen the domain using the appointment** (spec §2.2). An appointment for a child, or "accompanied", tells Earshot in advance to expect a parent or carer. That person becomes an extra voice, chosen with the same candidate-voice mechanism (spec §6.4), with the role-based permissions above.

## 2. Voices and doses
- **Re-commit:** if the voice chosen as the patient stops answering while another voice keeps answering the doctor, propose switching (spec L6).
- **Cumulative dose:** what the patient has already taken plus what is prescribed (e.g. the patient took paracetamol this morning and the doctor prescribes 3 g/day).
- **Drug interactions,** and doses for children or calculated from body weight.
- **Live retrieval for the whole BDPM catalogue** (beyond the demo drugs), with pharmacist review of the extracted limits.

## 3. Other roadmap items (from spec §13 and §17.3)
- A microphone worn by the doctor, combined with a check that the doctor is the loudest on it. This is the main fix for replayed or cloned voices and for the stage sound system.
- Anti-spoofing for cloned voices, and a random phrase the doctor reads aloud for high-risk prescriptions.
- Teleconsultation audio (compressed, one channel per person).
- An offline speaker-separation pass over the whole recording as part of the final check (pyannote community-1). It may only downgrade labels, never upgrade them.
- Full certified health-data hosting (HDS) and on-device storage of voiceprints.
- An SDK for scribe vendors.
