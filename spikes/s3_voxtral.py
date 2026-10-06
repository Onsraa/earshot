"""S3 throwaway: Voxtral on 20 French medical sentences (synthetic TTS for now; re-run on real voices), with and
without drug-name context_bias; checks drug names + numbers survive and word timestamps come back. Needs MISTRAL_API_KEY."""
import io, json, os, pathlib, sys
import soundfile as sf
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from s1a_synth import tts, VOICES, SR
from mistralai.client import Mistral

SENT = ["Vous allez prendre du paracétamol, trois fois mille milligrammes par jour.", "Hier j'en ai pris quatre, des quatre cents.",
        "Je vous prescris de l'amoxicilline, mille milligrammes deux fois par jour pendant six jours.", "On arrête le tramadol.",
        "Le Kardegic soixante-quinze, on continue.", "Je vous mets en arrêt deux semaines.", "Prenez du Doliprane mille matin, midi et soir.",
        "Pas plus de trois grammes par jour.", "De l'ibuprofène quatre cents, toutes les huit heures.", "Je vous fais une ordonnance pour une prise de sang.",
        "Si la fièvre dure plus de cinq jours, on fera une prise de sang.", "Elle m'a conseillé de reprendre le travail dans trois jours.",
        "Un demi comprimé de Lexomil le soir.", "Azithromycine cinq cents milligrammes le premier jour.", "Je renouvelle le Levothyrox pour trois mois.",
        "J'ai pris cinq mille milligrammes de Doliprane hier.", "Je pensais reprendre lundi.", "Spasfon, deux comprimés trois fois par jour.",
        "Augmentin un gramme, matin et soir, pendant sept jours.", "Ventoline, deux bouffées en cas de gêne respiratoire."]
HINTS = ["paracétamol", "Doliprane", "ibuprofène", "Advil", "tramadol", "amoxicilline", "Kardegic", "Lexomil", "azithromycine", "Levothyrox",
         "Spasfon", "Augmentin", "Ventoline", "milligrammes"]
c = Mistral(api_key=os.environ["MISTRAL_API_KEY"]); out = []
for i, s in enumerate(SENT):
    buf = io.BytesIO(); sf.write(buf, tts(VOICES["DOCTOR"], s), SR, format="WAV")
    for bias in (None, HINTS):
        r = c.audio.transcriptions.complete(model="voxtral-mini-latest", file={"content": buf.getvalue(), "file_name": f"s{i}.wav"},
                                            timestamp_granularities=["word"], context_bias=bias)
        out.append({"ref": s, "bias": bias is not None, "hyp": r.text, "language": r.language, "n_words_ts": len(r.segments or [])})
        print(f"{'bias' if bias else 'raw '} | {s}\n     -> {r.text}  (lang={r.language}, word timestamps={len(r.segments or [])})")
pathlib.Path(__file__).with_name("s3_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
