# Earshot: models

Each row is a job Earshot needs done. ✓ means verified on 2026-10-06, either by installing and running it on the demo Mac or by reading the official docs. Everything else is marked as something to verify.

## Overview
| Job | Model / tool | Runs on | Version / id | Tier | Status |
|---|---|---|---|---|---|
| Detect speech, cut sentences | Silero VAD (`VADIterator`) | Mac CPU | `silero-vad` 6.2.3 | 1 | ✓ installed; streaming signature `VADIterator(model, threshold=0.5, sampling_rate=16000, min_silence_duration_ms, speech_pad_ms)` |
| Voice fingerprint | SpeechBrain ECAPA-TDNN | Mac CPU (MPS available) | `speechbrain/spkrec-ecapa-voxceleb`, speechbrain 1.1.1 | 1 | ✓ ran in the synthetic dry run (192-dimensional vectors) |
| Voice fingerprint (alternative) | WeSpeaker ResNet34-LM | Mac | `pyannote/wespeaker-voxceleb-resnet34-LM` | 1 (S1a decides) | needs `HF_TOKEN`; not tested |
| Speech → text | Mistral Voxtral Mini Transcribe 2 | Mistral API | `voxtral-mini-latest` | 1 | ✓ API and SDK read (mistralai 3.0.0); not yet called (no key) |
| Speech → text (fallback) | Whisper large-v3-turbo (mlx-whisper or faster-whisper) | Mac (MPS) | — | 1 | not installed yet; set up at hour 0 |
| Per-sentence questions | Jev | TypeSafe API | `jev-latest` | 1 | ✓ API docs read; not yet called (no key) |
| Questions (fallback) and naive scribe | Mistral Large | Mistral API | `mistral-large-latest` | 1 | ✓ SDK signature read; not yet called |
| Scribe (alternative) | Claude via AWS Bedrock | AWS | to choose | 1 (S5 decides) | not tested |
| Number words → digits | text2num `alpha2digit` | Mac | text2num 3.1.0 | 1 | ✓ tested on 30 phrases (S8) |
| Second check (negation, hypothesis, reported speech) | EDS-NLP qualifiers | Mac | edsnlp 0.23.0 (spaCy 3.8.16) | 2 | ✓ installed; pipe names checked at the event |
| Speaker change / overlap | pyannote segmentation-3.0 | Mac | pyannote.audio 4.0.7 | 2 | ✓ installable; needs `HF_TOKEN` and accepting the model's conditions |
| TV / radio tag | YAMNet (AudioSet classes "Television", "Radio") | Mac | — | 3 | to choose the runtime in S6 |
| Drug limits | *data, not a model*: BDPM + RCP §4.2 → `drug_limits.json` | — | 2026-10-06 extraction | 1 | ✓ numbers checked against their quotes |
| Search for drugs outside the table | keyword match on the substance, then `mistral-embed` semantic search over cached RCP sections; LLM extraction with the quote check | API | — | 2 | to build |

## Details

### Voice: ECAPA-TDNN (SpeechBrain)
- **Why:** it's a mature, CPU-friendly model that produces 192-number fingerprints. It installs with pip and needs no token. The 2025–2026 alternatives were rejected (spec §17.3).
- **How we use it:**
  - one L2-normalized embedding per segment;
  - cosine similarity against the doctor's templates and the patient's templates;
  - the best match across templates wins.
- **Known weak spots:**
  - segments under about 1.5 s (handled with UNCERTAIN under 1 s, plus per-duration thresholds in Tier 2);
  - a far-away or echoing microphone (handled by recording the doctor at the demo spot).
- **Thresholds:** they all come from S1a. The synthetic voices aren't representative: in the dry run the doctor's voice scored 0.81–0.94 against itself, and other voices scored 0.36–0.65.
- **Lesson from the dry run:** some macOS voices are aliases of each other (Jacques = Eddy). Never use them as two different "people" in a test.

### Speech to text: Voxtral Mini Transcribe 2
- **Call:**

  ```python
  from mistralai.client import Mistral
  client.audio.transcriptions.complete(
      model="voxtral-mini-latest",
      file={"content": wav_bytes, "file_name": "s.wav"},
      timestamp_granularities=["word"],
      context_bias=hints,
  )
  ```

  It returns `TranscriptionResponse{text, language, segments[{text, start, end, type, score, speaker_id}]}`.
- **Constraint:** `timestamp_granularities` and `language` can't be used together, so with word timestamps the language is detected automatically. **Check `language == "fr"` on every response.** If it isn't French, treat the sentence as UNCERTAIN.
- **Price:** $0.003 per minute (Mistral, February 2026). A 75-second demo costs about $0.004.
- **We don't use its speaker separation (`diarize`):** it labels speakers from the audio stream, not from the doctor's enrolled voice. Spec §6.4: the doctor's voice is the only source of authority.
- **Voxtral Realtime** (open weights, 4B parameters) can run on the Mac. It isn't used: it's unverified on this machine, and the batch model is enough for per-sentence transcription.

### Per-sentence questions: Jev
- **Why:** questions are typed (`noul` = yes/no probability, `choice` = one of a list) and come back with a confidence. They're cheap. **All the questions about one sentence go in one call, and the input is billed only once**, which is exactly our per-sentence pattern.
- **Call:**
  - request: `POST https://api.typesafe.ai/v1/systemone` with header `Authorization: Bearer $JEV_API_KEY` and body `{"state", "model":"jev-latest", "questions":{…}}`;
  - response: `answers[id]`, which is `{noul}` or `{choice, probabilities, confidence}`.
- **Known weak spots** (from `../../docs/ideas.md`):
  - adversarial text can push its answers around;
  - its confidence is uneven across tasks;
  - it's weak with numbers and dates;
  - it handles text only.

  **How we contain this:**
  - only doctor sentences can grant authority;
  - all numbers and dates are handled in code;
  - a low-confidence answer is either sent to the LLM or turned into 🟠;
  - spotlighting (spec §6.6).
- **Not documented:** French support and token limits. S4 measures French.
- **Errors:** 401, 422, 429 (back off and retry), 529. In our code these map to `ServiceDown`, and `RoutedClient` then sends the question to the LLM.

### LLM: Mistral Large (fallback questions and naive scribe)
- **Why:** it's French, it supports JSON mode, and it's sovereign, which fits the pitch. The alternative is Claude on Bedrock, which would use the AWS partner credits.
- **Call:** `client.chat.complete(model="mistral-large-latest", messages=…, response_format={"type":"json_object"}, temperature=0)`.
- **Settings:**
  - `temperature=0` everywhere;
  - every prompt is versioned (`prompt_version` in `config/models.json`);
  - offline mode replays the cached answers.

### Normalizer: text2num plus our own code
- `alpha2digit(text, "fr", threshold=0)` turns number words into digits, so "trois fois mille milligrammes" becomes "3 fois 1000 milligrammes".
- **Quirks:**
  - "un demi" becomes "1 demi", so handle "demi" **first**;
  - decimals come out with a comma ("0,5").
- **Our own code covers the rest** (see `test-results.md` S8): units, frequencies, durations, weekdays, "jusqu'au N", counts × strength.

### Tier 2 / Tier 3 models
- **pyannote segmentation-3.0:**
  - setup: `Model.from_pretrained("pyannote/segmentation-3.0", token=HF_TOKEN)` (check the argument name for pyannote 4.x at the event);
  - input: 10-second windows;
  - output: 7 classes, including overlapping speakers.
- **EDS-NLP qualifiers:** they need a term matcher upstream (the action terms) so they have something to qualify.
- **YAMNet:** either the TensorFlow Hub model or a PyTorch port. Choose in S6; skip it if it's heavy or unreliable.

## Models we considered and set aside (spec §17.3)
Each of these was dropped for one or more of the same reasons:
- weak or untested in French;
- offline-only, or needs a GPU;
- its licence rules out commercial use;
- it can't identify the *doctor* specifically.

They are:
- Streaming Sortformer and Nemotron 3 Diarization;
- DiariZen, DiCoW and SpeakerLM;
- DiarizationLM, and any model that infers who is speaking from the text;
- NeMo text normalization;
- dateparser for dates;
- anti-spoofing detectors.
