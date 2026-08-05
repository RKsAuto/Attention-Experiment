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

## Deploying (free, on Render)

The `Dockerfile` bundles python plus espeak so the speech engine is there on
the server too. `render.yaml` tells Render how to run it.

1. Sign in at https://render.com with GitHub.
2. **New → Web Service**, pick this repo, and choose the `dev` branch.
3. Render reads `render.yaml`, so just confirm: runtime Docker, plan Free.
4. Click **Create**. The first build takes a few minutes.

Render gives you a URL like `https://attention-experiment.onrender.com`.
Open `.github/workflows/keep-alive.yml` and put that URL in `SITE_URL`.

## Keeping it awake

Free services sleep after 15 idle minutes and then take ~50 seconds to wake
up, which is a bad first impression for someone taking the test. The workflow
in `.github/workflows/keep-alive.yml` pings `/health` every 10 minutes to stop
that, and doubles as monitoring: if the site is down the ping fails and GitHub
emails you about the failed run. This repo is public so those runs are free.

Two things worth knowing:

- Scheduled workflows only run from the default branch, so the file has to be
  on `dev` before it does anything.
- GitHub pauses scheduled workflows after 60 days without any repo activity.
  It sends a warning email first, and one click re-enables it.
