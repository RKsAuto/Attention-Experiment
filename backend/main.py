import mimetypes
import os
import threading
import time
import urllib.request
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from audio_generation import (
    SPEECH_RATE,
    current_voice,
    make_stereo,
    reverse_words,
    text_to_wav,
)

# Slim server images often ship without the system mime table, and then these
# get labelled text/plain and the browser refuses to use them. Spell them out.
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("text/javascript", ".js")

BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "audio"
FORWARD = AUDIO_DIR / "forward.wav"
REVERSED = AUDIO_DIR / "reversed.wav"

app = FastAPI(title="Attention Experiment")


@app.middleware("http")
async def always_fresh_frontend(request, call_next):
    """Phones were still showing an old style.css for a while after a deploy.
    Ask the browser to check with us each time; these files are tiny, and it
    still gets a cheap 304 back when nothing actually changed."""
    response = await call_next(request)
    if not request.url.path.startswith(("/audio", "/generate")):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/health")
def health():
    """Also reports the voice actually in use, so you can tell at a glance
    whether a deploy really picked up a voice change."""
    return {
        "status": "awake",
        "voice": current_voice(),
        "rate": SPEECH_RATE,
    }


@app.post("/generate")
def generate(text: str = Body(..., embed=True)):
    text = text.strip()
    if not text:
        raise HTTPException(400, "Paste some text first")
    AUDIO_DIR.mkdir(exist_ok=True)
    text_to_wav(text, str(FORWARD))
    text_to_wav(reverse_words(text), str(REVERSED))
    return {"status": "ready"}


def pick_source(flipped):
    """Flipped ears hear the word-reversed audio, others hear the original."""
    path = REVERSED if flipped else FORWARD
    if not path.exists():
        raise HTTPException(404, "No audio yet, hit Generate first")
    return str(path)


@app.get("/audio/left")
def left_ear(flip: bool = False):
    out = AUDIO_DIR / "left.wav"
    make_stereo(pick_source(flip), None, str(out))
    return FileResponse(out, media_type="audio/wav")


@app.get("/audio/right")
def right_ear(flip: bool = False):
    out = AUDIO_DIR / "right.wav"
    make_stereo(None, pick_source(flip), str(out))
    return FileResponse(out, media_type="audio/wav")


@app.get("/audio/both")
def both_ears(flipL: bool = False, flipR: bool = False):
    out = AUDIO_DIR / "both.wav"
    make_stereo(pick_source(flipL), pick_source(flipR), str(out))
    return FileResponse(out, media_type="audio/wav")


def keep_awake(url):
    """Render sleeps a free service after 15 idle minutes, so knock on our own
    public door every 10. Only prevents sleeping, cannot wake us back up."""
    while True:
        time.sleep(600)
        try:
            urllib.request.urlopen(url + "/health", timeout=30).close()
        except Exception:
            pass  # a missed ping is not worth crashing the app over


# RENDER_EXTERNAL_URL is set by Render, so this stays off on your own machine
SELF_URL = os.environ.get("RENDER_EXTERNAL_URL")
if SELF_URL:
    threading.Thread(target=keep_awake, args=(SELF_URL,), daemon=True).start()


# serve the frontend as-is from the same server, so no CORS fuss
app.mount("/", StaticFiles(directory=BASE_DIR.parent / "frontend", html=True))
