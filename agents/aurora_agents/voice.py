"""Voice for approved advisory text: Cloud Text-to-Speech with Gemini-TTS (AI_AGENTS §1, §5.5).

Speaks the rendered ``voice_script`` of an advisory (numbers already inserted by code; the voice
model only reads). Telugu and Hindi are GA for gemini-2.5-flash-tts on Google Cloud. Audio is
cached by input hash, so a replay is identical and costs nothing after the first request.
"""

import base64
import hashlib
import os
from typing import Any

from google.cloud import texttospeech

from .gemini import Cache

TTS_MODEL = os.environ.get("TTS_VOICE_MODEL", "gemini-2.5-flash-tts")
VOICE = os.environ.get("TTS_VOICE_NAME", "Kore")
STYLE = (
    "Read this as a calm, clear official advisory for district disaster officials, "
    "at a steady pace."
)
LANGS = {"en-IN", "te-IN", "hi-IN"}


def speak(text: str, language: str, cache: Cache) -> dict[str, Any]:
    """MP3 of ``text`` in ``language``, as base64, with the model and voice used."""
    if language not in LANGS:
        raise ValueError(f"no voice for {language}")
    key = (
        "tts-"
        + hashlib.sha256("|".join([TTS_MODEL, VOICE, STYLE, language, text]).encode()).hexdigest()
    )
    if (hit := cache.get(key)) is not None:
        return {**hit["output"], "cached": True}
    client = texttospeech.TextToSpeechClient()
    resp = client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text, prompt=STYLE),
        voice=texttospeech.VoiceSelectionParams(
            language_code=language, name=VOICE, model_name=TTS_MODEL
        ),
        audio_config=texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3),
    )
    out = {
        "audio_b64": base64.b64encode(resp.audio_content).decode(),
        "mime": "audio/mpeg",
        "model": TTS_MODEL,
        "voice": VOICE,
        "language": language,
    }
    cache.put(key, {"output": out})
    return {**out, "cached": False}
