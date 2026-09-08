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

# The two text boxes on the page. Each is spoken forwards and backwards, and
# either recording can go to either ear, which is what lets the two ears hear
# entirely different things.
BOXES = ("a", "b")

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


def clip(box, flipped):
    return AUDIO_DIR / f"{box}_{'reversed' if flipped else 'forward'}.wav"


@app.post("/generate")
def generate(a: str = Body("", embed=True), b: str = Body("", embed=True)):
    """Speak whichever boxes were filled in, each one both ways round."""
    texts = {"a": a.strip(), "b": b.strip()}
    if not any(texts.values()):
        raise HTTPException(400, "Paste some text first")

    AUDIO_DIR.mkdir(exist_ok=True)
    for stale in AUDIO_DIR.glob("*.wav"):
        stale.unlink()  # so an emptied box cannot keep playing its old audio

    for box, text in texts.items():
        if text:
            text_to_wav(text, str(clip(box, False)))
            text_to_wav(reverse_words(text), str(clip(box, True)))
    return {"status": "ready", "ready": [b for b, t in texts.items() if t]}


def pick(box, flipped):
    """The recording an ear should play, or None to leave that ear silent."""
    if not box:
        return None
    if box not in BOXES:
        raise HTTPException(400, f"There is no box called {box}")
    path = clip(box, flipped)
    if not path.exists():
        raise HTTPException(404, f"Box {box.upper()} is empty, hit Generate first")
    return str(path)


@app.get("/audio")
def audio(left: str = "", right: str = "",
          left_flip: bool = False, right_flip: bool = False):
    """Either box can feed either ear, so the ears can differ completely."""
    if not left and not right:
        raise HTTPException(400, "Pick something for at least one ear")
    out = AUDIO_DIR / f"play_{left}{left_flip}_{right}{right_flip}.wav"
    make_stereo(pick(left, left_flip), pick(right, right_flip), str(out))
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
