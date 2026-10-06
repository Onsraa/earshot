"""S1a throwaway: build SYNTHETIC takes (macOS `say`) to dry-run the analysis plumbing. Not an accuracy test."""
import json, pathlib, subprocess, tempfile
import numpy as np, soundfile as sf

SR = 16000
OUT = pathlib.Path(__file__).resolve().parents[1] / "fixtures/audio/synth"
VOICES = {"DOCTOR": "Jacques", "PATIENT": "Flo (French (France))", "OTHER": "Grandpa (French (France))"}
SCRIPT = [
    ("DOCTOR", "Bonjour, installez-vous. Qu'est-ce qui vous amène aujourd'hui ?"),
    ("PATIENT", "Bonjour docteur. Depuis trois jours j'ai de la fièvre, autour de trente-neuf, mal à la tête, des courbatures partout. Je suis vraiment épuisé."),
    ("DOCTOR", "D'accord. Vous avez pris quelque chose pour la fièvre ?"),
    ("PATIENT", "Oui, ma mère travaille en pharmacie, elle me donne souvent de l'ibuprofène. Hier j'en ai pris quatre, des quatre cents. Et elle m'a conseillé de reprendre le travail dans trois jours."),
    ("DOCTOR", "Je vais vous examiner. Respirez fort par la bouche."),
    ("DOCTOR", "Bon, c'est une grippe. Non, l'ibuprofène on arrête, avec de la fièvre ce n'est pas une bonne idée. Vous allez prendre du paracétamol, trois fois mille milligrammes par jour, et vous reposer deux semaines. Je vous fais un arrêt."),
    ("PATIENT", "Deux semaines ? Je pensais reprendre lundi."),
    ("DOCTOR", "Non, deux semaines de repos, c'est important. Si la fièvre dure plus de cinq jours, on fera une prise de sang."),
]
TV = ("OTHER", "Contre la fièvre, l'ibuprofène quatre cents, jusqu'à trois fois par jour. Demandez conseil à votre pharmacien.")
ENROLL = [
    "Je suis le docteur Martin et je confirme que cette consultation est enregistrée pour la démonstration. "
    "Le patient est reçu au cabinet, je recueille ses symptômes, je l'examine, puis je décide du traitement et des documents à rédiger.",
    "La consultation de médecine générale suit toujours le même déroulé : l'accueil, le motif, l'interrogatoire, l'examen clinique, "
    "la conclusion et les prescriptions. Chaque décision est expliquée au patient avant d'être notée dans le dossier.",
]

def tts(voice, text):
    with tempfile.TemporaryDirectory() as d:
        aiff, wav = f"{d}/a.aiff", f"{d}/a.wav"
        subprocess.run(["say", "-v", voice, "-o", aiff, text], check=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", aiff, "-ar", str(SR), "-ac", "1", wav], check=True)
        x, _ = sf.read(wav, dtype="float32")
    return x

def silence(s): return np.zeros(int(s * SR), dtype="float32")

def take(name, lines, gap_reply=0.7, gap_same=1.0):
    audio, labels, t, prev = [], [], 0.0, None
    for spk, text in lines:
        g = gap_same if spk == prev else gap_reply
        audio.append(silence(g)); t += g
        x = tts(VOICES[spk], text); audio.append(x)
        labels.append({"start": round(t, 2), "end": round(t + len(x) / SR, 2), "speaker": spk, "text": text}); t += len(x) / SR
        prev = spk
    audio.append(silence(1.0))
    sf.write(OUT / f"{name}.wav", np.concatenate(audio), SR)
    (OUT / f"{name}.labels.json").write_text(json.dumps(labels, ensure_ascii=False, indent=1))
    print(name, f"{t:.1f}s", len(labels), "lines")

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for i, text in enumerate(ENROLL, 1):
        sf.write(OUT / f"doctor_enroll_{i}.wav", tts(VOICES["DOCTOR"], text), SR)
    take("script_take1", SCRIPT)
    take("tv_first_take", [TV] + SCRIPT, gap_reply=0.7)
