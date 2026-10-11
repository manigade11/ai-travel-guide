import base64
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from google import genai

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
app = Flask(__name__, static_folder=None)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing. Set it in your local .env or Vercel Environment Variables.")
if not MURF_API_KEY:
    raise RuntimeError("MURF_API_KEY is missing. Set it in your local .env or Vercel Environment Variables.")

client = genai.Client(api_key=GEMINI_API_KEY)

PROMPTS = {
    "Summary": """
You are a professional tourist guide. Give a high-level overview of "{place}" in {language}.
Focus on historical significance, why it is famous, and key architectural or cultural highlights.
Keep it concise, engaging, easy to follow, and around 200 words. Avoid excessive dates.
Respond only in {language}.
""",
    "Detailed": """
You are a professional tourist guide. Give a detailed, immersive explanation of "{place}" in {language}.
Cover historical background, architecture, cultural importance, notable events, interesting facts, and visitor insights.
Use clear storytelling and aim for around 400 words.
Respond only in {language}.
"""
}

VOICE_IDS = {
    "English": {"Male": "Matthew", "Female": "Alicia"},
    "Hindi": {"Male": "Aman", "Female": "Namrita"},
    "Tamil": {"Male": "Murali", "Female": "Iniya"},
    "Telugu": {"Male": "Zion", "Female": "Josie"},
}
LOCALES = {"English": "en-US", "Hindi": "hi-IN", "Tamil": "ta-IN", "Telugu": "te-IN"}

def generate_description(place: str, answer_type: str, language: str) -> str:
    prompt = PROMPTS[answer_type].format(place=place, language=language)
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return text.strip()

def generate_speech(text: str, voice_id: str, locale: str) -> bytes:
    url = "https://global.api.murf.ai/v1/speech/stream"
    headers = {"api-key": MURF_API_KEY, "Content-Type": "application/json"}
    payload = {
        "voice_id": voice_id,
        "text": text,
        "locale": locale,
        "model": "FALCON",
        "format": "MP3",
        "sampleRate": 24000,
        "channelType": "MONO",
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=(10, 180))
        if not response.ok:
            # Do not return an empty/invalid MP3 as if it were successful.
            detail = response.text[:500]
            raise RuntimeError(f"Murf API returned HTTP {response.status_code}: {detail}")
        return response.content
    except requests.RequestException as exc:
        raise RuntimeError(f"Could not connect to Murf API: {exc}") from exc

@app.get("/")
def home():
    return send_from_directory(PUBLIC_DIR, "index.html")

@app.get("/index.js")
def frontend_javascript():
    return send_from_directory(PUBLIC_DIR, "index.js")

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.post("/generate-audio-guide")
def generate_audio_guide():
    payload = request.get_json(silent=True) or {}
    place = payload.get("place")
    answer_type = payload.get("answerType", "Summary")
    language = payload.get("language", "English")

    if not isinstance(place, str) or not place.strip():
        return jsonify({"error": "Please provide a destination in 'place'."}), 400
    if answer_type not in PROMPTS:
        return jsonify({"error": "answerType must be 'Summary' or 'Detailed'."}), 400
    if language not in VOICE_IDS:
        return jsonify({"error": f"Unsupported language. Choose one of: {', '.join(VOICE_IDS)}."}), 400

    # Derive voice and locale on the server rather than trusting arbitrary client values.
    voice_gender = payload.get("voice", "Male")
    if voice_gender not in ("Male", "Female"):
        return jsonify({"error": "voice must be 'Male' or 'Female'."}), 400
    voice_id = VOICE_IDS[language][voice_gender]
    locale = LOCALES[language]

    try:
        description = generate_description(place.strip(), answer_type, language)
        audio_bytes = generate_speech(description, voice_id, locale)
        encoded_audio = base64.b64encode(audio_bytes).decode("ascii")
        return jsonify({"description": description, "audioBase64": encoded_audio})
    except Exception as exc:
        app.logger.exception("Audio guide generation failed")
        return jsonify({"error": str(exc)}), 502

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
