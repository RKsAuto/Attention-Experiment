This is a website designed to perform an attention experiment in which we play an audio for the text pasted in the an ear and it is played reversed in the other ear and we check the the attention of the individual by asking him the questions related to what he understood from the both the audios.

## How to run

```
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --reload
```

Then open http://127.0.0.1:8000 in your browser and put your headphones on.

There are two text boxes, so the two ears can carry entirely different
stimuli. Fill in one or both and hit **Generate Audio** (the speech is made
offline, no API keys needed).

- Each box has its own **L** and **R**: they play *that box* into that ear
  alone, with the other ear silent. Handy for auditioning one stimulus.
- **B** is the dichotic one: the first box goes to the left ear and the second
  to the right, both at once.
- Each box has its own **flip** tick, which makes that box play word-reversed
  ("I am groot" becomes "groot am I").
- **P** pauses whatever is playing and resumes from the same spot. Its face
  shows what pressing it will do next.

For the original single-passage version of the experiment, paste the same text
into both boxes and tick **flip** on one of them. Both takes then come out the
same length, so the ears stay word-aligned.

macOS uses the built-in `say` command, so nothing extra is needed there.
Everywhere else it speaks through espeak-ng: `sudo apt install espeak-ng` on
Linux, or the installer from https://github.com/espeak-ng/espeak-ng on Windows.

## How the words are spoken

Each word is separated by a comma before it reaches the speech engine. Without
that, espeak runs unstressed words together — it says "I am groot" as a single
blurred sound and the "I" effectively vanishes, which is fatal for a shadowing
task. Commas make it stress every word on its own.

It also keeps the two ears in step. Spoken plainly, "I am groot" and "groot am
I" come out 261ms apart, so the ears drift; one word per comma makes both takes
exactly the same length, and the words stay aligned the whole way through.

There is a short silence at the start of every clip too, because browsers tend
to clip the first moment of playback and a one-syllable opening word gets lost.

## Tuning the voice

Two environment variables, so the stimulus can be adjusted without a redeploy:

- `SPEECH_RATE` — words per minute, default 160. The engines sit near 200 on
  their own, which is far too quick for a participant to shadow. It is a dial
  rather than an exact figure and each voice reads it a little differently;
  160 measures at about 96 wpm with the default voice.
- `VOICE` — an espeak-ng voice, default `mb-us1`, the mbrola american female.
  `espeak-ng --voices` and `espeak-ng --voices=mbrola` list the rest. Not used
  on macOS, which speaks through its own much nicer system voices.
- `CUE_HZ` — pitch of the tone that opens every clip, default 880. Set it to 0
  to drop the tone. `CUE_SECONDS` (default 0.25) and `CUE_LEVEL` (default 0.25,
  a share of full volume) control its length and loudness.
- `LEAD_IN` — the gap between the tone and the first word, default 0.5.
- `TAIL_OUT` — quiet after the last word, default 0.5.

### Why there is a tone

A bluetooth headset drops its link between clips and sleeps straight through
digital silence. Padding the front of a clip with quiet therefore does nothing:
a whole second of silence changed nothing at all, because silence is precisely
what the headset ignores, and it woke on the first word and swallowed it. A
real sound wakes it, and after the gap it is alert by the time the speech
begins. A warning tone ahead of a trial is normal in listening experiments
anyway. Wired listeners do not need it: `CUE_HZ=0`.

`mb-us1` needs the `mbrola` and `mbrola-us1` packages, which is why the image
is built on Ubuntu rather than a slim Python base: both live in Ubuntu's
multiverse component, which the Dockerfile enables. If they are ever missing
the app falls back to plain `en-us` rather than failing, so a packaging problem
costs voice quality instead of taking the site down — and `/health` reports
which voice is really in use, so you can tell the two apart. To hear it locally
on Ubuntu: `sudo apt install mbrola mbrola-us1`.

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
