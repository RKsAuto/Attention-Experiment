This is a website designed to perform an attention experiment in which we play an audio for the text pasted in the an ear and it is played reversed in the other ear and we check the the attention of the individual by asking him the questions related to what he understood from the both the audios.

## How to run

```
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --reload
```

Then open http://127.0.0.1:8000 in your browser and put your headphones on.

- Paste a paragraph and hit **Generate Audios** (the speech is made offline, no API keys needed).
- **L** plays the left ear only, **R** the right ear only, **B** plays both together.
- Tick **flip** under an ear to make that ear hear the word-reversed version
  ("I am groot" becomes "groot am I").

On Linux the speech engine needs espeak once: `sudo apt install espeak-ng`.
On macOS and Windows nothing extra is needed.
