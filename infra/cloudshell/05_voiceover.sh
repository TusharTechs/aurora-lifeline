#!/usr/bin/env bash
# Demo-video narration with Cloud Text-to-Speech Gemini-TTS (male voice), one WAV per scene.
# Run in Cloud Shell:
#   cd ~/aurora-lifeline && git pull && bash infra/cloudshell/05_voiceover.sh
# Then download the zip it names (Cloud Shell: "cloudshell download <path>").
# Cost: about 4.5 minutes of synthesis, a few cents.
set -euo pipefail
PROJECT="${PROJECT:-aurora-lifeline}"
cd "$(git rev-parse --show-toplevel)"
test -x "$HOME/.aurora-venv/bin/python" || { echo "run 01_bootstrap.sh first" >&2; exit 1; }
"$HOME/.aurora-venv/bin/pip" install -q "google-cloud-texttospeech>=2.37"
OUT="$HOME/aurora-voiceover"
rm -rf "$OUT" && mkdir -p "$OUT"
GOOGLE_CLOUD_PROJECT="$PROJECT" "$HOME/.aurora-venv/bin/python" - "$OUT" <<'PY'
import json, sys, time, wave
from pathlib import Path
from google.cloud import texttospeech as tts

out = Path(sys.argv[1])
spec = json.loads(Path("video/narration.json").read_text())
client = tts.TextToSpeechClient()
models = ["gemini-2.5-pro-tts", "gemini-2.5-flash-tts"]

def synth(text: str, model: str) -> bytes:
    r = client.synthesize_speech(
        input=tts.SynthesisInput(text=text, prompt=spec["style"]),
        voice=tts.VoiceSelectionParams(language_code=spec["language"], name=spec["voice"], model_name=model),
        audio_config=tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16, sample_rate_hertz=24000),
    )
    return r.audio_content

used = None
for s in spec["scenes"]:
    for model in ([used] if used else models):
        try:
            audio = synth(s["text"], model)
            used = model
            break
        except Exception as e:  # fall back to the flash model once
            print(f"{s['id']}: {model} failed ({type(e).__name__}: {str(e)[:120]})")
    else:
        sys.exit(f"{s['id']}: no model worked")
    f = out / f"{s['id']}.wav"
    f.write_bytes(audio)
    with wave.open(str(f)) as w:
        print(f"{s['id']}: {w.getnframes() / w.getframerate():5.1f} s  ({used})")
    time.sleep(0.5)
(out / "voice.json").write_text(json.dumps({"model": used, "voice": spec["voice"], "language": spec["language"]}))
PY
cd "$HOME" && rm -f aurora-voiceover.zip && zip -qr aurora-voiceover.zip aurora-voiceover
echo
echo "Done. Download it with:"
echo "  cloudshell download $HOME/aurora-voiceover.zip"
