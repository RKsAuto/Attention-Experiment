import mimetypes
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from audio_generation import make_stereo, reverse_words, text_to_wav

# Slim server images often ship without the system mime table, and then these
# get labelled text/plain and the browser refuses to use them. Spell them out.
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("text/javascript", ".js")

BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "audio"
FORWARD = AUDIO_DIR / "forward.wav"
REVERSED = AUDIO_DIR / "reversed.wav"

app = FastAPI(title="Attention Experiment")


@app.get("/health")
def health():
    return {"status": "awake"}


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


# serve the frontend as-is from the same server, so no CORS fuss
app.mount("/", StaticFiles(directory=BASE_DIR.parent / "frontend", html=True))
