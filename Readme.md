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

macOS uses the built-in `say` command, so nothing extra is needed there.
Everywhere else it speaks through espeak-ng: `sudo apt install espeak-ng` on
Linux, or the installer from https://github.com/espeak-ng/espeak-ng on Windows.

## Tuning the voice

Two environment variables, so the stimulus can be adjusted without a redeploy:

- `SPEECH_RATE` — words per minute, default 100. The engines sit near 200 on
  their own, which is far too quick for a participant to shadow. It is a dial
  rather than an exact figure and each voice reads it a little differently;
  100 measures at about 114 wpm with the default voice.
- `VOICE` — an espeak-ng voice, default `mb-us1`, the mbrola american female.
  `espeak-ng --voices` and `espeak-ng --voices=mbrola` list the rest. Not used
  on macOS, which speaks through its own much nicer system voices.

`mb-us1` needs the `mbrola` and `mbrola-us1` packages. The Dockerfile installs
them, switching on debian's non-free section first, because slim images ship
with it disabled. If they are ever missing the app quietly falls back to plain
`en-us` rather than failing, so a packaging problem costs voice quality instead
of taking the site down. To hear it locally on Ubuntu:
`sudo apt install mbrola mbrola-us1`.

## Deploying (free, on Render)

The `Dockerfile` bundles python plus espeak so the speech engine is there on
the server too. `render.yaml` tells Render how to run it.

1. Sign in at https://render.com with GitHub.
2. **New → Blueprint**, pick this repo, and choose the `dev` branch.
   (Blueprint is the flow that actually reads `render.yaml`. If you use
   **New → Web Service** instead, set runtime to Docker and plan to Free
   by hand, and point the health check at `/health`.)
3. Click **Apply**. The first build takes a few minutes.

Render gives you a URL like `https://attention-experiment.onrender.com`.
Open `.github/workflows/keep-alive.yml` and put that URL in `SITE_URL`.

## Keeping it awake

Free services sleep after 15 idle minutes and then take ~50 seconds to wake
up, which is a bad first impression for someone taking the test. There are two
layers guarding against that, because neither is enough on its own.

**1. The app pings itself.** `keep_awake` in `main.py` requests its own public
`/health` every 10 minutes, which counts as traffic and resets the idle timer.
It switches on only when `RENDER_EXTERNAL_URL` exists, so running locally is
unaffected. The catch: it can stop the app falling asleep but cannot wake it
once it has, so after a deploy or restart during a quiet spell something else
has to knock first.

**2. An outside pinger.** `.github/workflows/keep-alive.yml` asks GitHub to
ping every 10 minutes, but GitHub throttles frequent scheduled workflows hard.
Measured over one 11 hour stretch it fired 4 times, not 66, with gaps as long
as 6 hours. Treat it as a backup, not the plan.

For dependable uptime and real alerts, point a free monitor at the site:

- https://uptimerobot.com (free plan, checks every 5 minutes) or
  https://cron-job.org (free, can go as often as every minute).
- Add a monitor for `https://<your-render-url>/health` and give it your email.

That both keeps the service warm and actually tells you when it is down, which
is the part a cron job alone was never going to do.

Also worth knowing: GitHub pauses scheduled workflows after 60 days without
repo activity. It emails a warning first, and one click re-enables it.
