import math
import os
import struct
import subprocess
import sys
import wave

# Words per minute. The engines run near 200 on their own, which is too quick
# to shadow: the listener falls behind and stops tracking either ear. This is a
# dial rather than an exact figure, and each voice reads it slightly
# differently, so 100 lands at about 114 wpm with the default voice.
SPEECH_RATE = int(os.environ.get("SPEECH_RATE", 160))

# Which espeak-ng voice to speak with, on linux. mb-us1 is the mbrola american
# female, which is a good deal less buzzy than plain espeak but needs the
# mbrola packages. `espeak-ng --voices` lists the alternatives.
VOICE = os.environ.get("VOICE", "mb-us1")

# Always present, so it is what we drop back to if VOICE cannot be spoken
FALLBACK_VOICE = "en-us"


# Every clip opens with a short tone, then a gap, then the speech.
#
# The tone is not decoration. A bluetooth headset drops its link between clips
# and sleeps straight through digital silence, so padding the front with quiet
# never wakes it: a full second of silence made no difference, because silence
# is exactly what it ignores. Real sound wakes it, and by the time the gap has
# passed it is fully awake and the opening word survives. A warning tone before
# a trial is ordinary practice in listening experiments in any case.
#
# Set CUE_HZ to 0 for no tone, e.g. for wired listeners.
CUE_HZ = float(os.environ.get("CUE_HZ", 880))
CUE_SECONDS = float(os.environ.get("CUE_SECONDS", 0.25))
CUE_LEVEL = float(os.environ.get("CUE_LEVEL", 0.25))  # share of full volume

# The gap between the tone and the first word, and the quiet after the last one
LEAD_IN_SECONDS = float(os.environ.get("LEAD_IN", 0.5))
TAIL_OUT_SECONDS = float(os.environ.get("TAIL_OUT", 0.5))


def reverse_words(text):
    return " ".join(reversed(text.split()))


def one_word_at_a_time(text):
    """Put a comma between every word before speaking it.

    espeak runs unstressed words together: it renders "I am groot" as one
    blurred "aIa#m gr'u:t", and the "I" all but disappears. Commas make it
    stress each word on its own. It also makes the forward and reversed takes
    come out to exactly the same length, so the two ears stay in step.
    """
    return ", ".join(text.split())


def current_voice():
    """What we will actually speak with, which is not always what was asked
    for: mbrola voices need extra packages that may not be installed."""
    if sys.platform == "darwin":
        return "macos say"
    listed = subprocess.run(
        ["espeak-ng", "--voices=mbrola" if VOICE.startswith("mb-") else "--voices"],
        capture_output=True, text=True,
    ).stdout
    return VOICE if f" {VOICE} " in listed or f"/{VOICE}" in listed else FALLBACK_VOICE


def text_to_wav(text, path):
    """Speak the text into a mono wav file, fully offline."""
    text = one_word_at_a_time(text)
    if sys.platform == "darwin":
        # macOS ships with the `say` command, no extra install needed
        subprocess.run(
            ["say", "-r", str(SPEECH_RATE), "-o", path,
             "--file-format=WAVE", "--data-format=LEI16@22050"],
            input=text.encode(),
            check=True,
        )
    else:
        # espeak-ng directly rather than through pyttsx3: it lets us name the
        # voice, and the text goes in on stdin so a long pasted paragraph
        # cannot run past the command line length limit.
        # If the mbrola packages are missing we still want working audio, so
        # fall back to the plain voice rather than failing the request.
        for voice in (VOICE, FALLBACK_VOICE):
            spoken = subprocess.run(
                ["espeak-ng", "--stdin", "-v", voice,
                 "-s", str(SPEECH_RATE), "-w", path],
                # the trailing newline matters: without it espeak cuts the
                # last word short, which ate the "I" in "groot am I"
                input=(text + "\n").encode(),
            )
            if spoken.returncode == 0:
                return
        raise RuntimeError("espeak-ng could not produce any audio")


def cue_tone(framerate, width):
    """The waking beep, in both ears, faded at each end so it does not click."""
    if not CUE_HZ or width != 2:  # 16 bit is all we ever produce
        return b""
    total = int(framerate * CUE_SECONDS)
    fade = max(1, int(framerate * 0.02))
    tone = bytearray()
    for i in range(total):
        loudness = min(1.0, i / fade, (total - i) / fade)
        sample = int(CUE_LEVEL * 32767 * loudness
                     * math.sin(2 * math.pi * CUE_HZ * i / framerate))
        tone += struct.pack("<h", sample) * 2
    return bytes(tone)


def read_wav(path):
    with wave.open(path, "rb") as w:
        return w.getparams(), w.readframes(w.getnframes())


def make_stereo(left_path, right_path, out_path):
    """Merge two mono wavs into one stereo wav.

    Pass None for a side to keep that ear silent.
    """
    params, _ = read_wav(left_path or right_path)
    left = read_wav(left_path)[1] if left_path else b""
    right = read_wav(right_path)[1] if right_path else b""

    # pad the shorter side with silence so both ears end together
    length = max(len(left), len(right))
    left = left.ljust(length, b"\x00")
    right = right.ljust(length, b"\x00")

    # a stereo frame is one left sample followed by one right sample
    width = params.sampwidth
    frames = bytearray(2 * length)
    for i in range(width):
        frames[i::2 * width] = left[i::width]
        frames[width + i::2 * width] = right[i::width]

    quiet = lambda seconds: b"\x00" * (int(params.framerate * seconds) * width * 2)

    with wave.open(out_path, "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(width)
        out.setframerate(params.framerate)
        out.writeframes(cue_tone(params.framerate, width)
                        + quiet(LEAD_IN_SECONDS) + bytes(frames)
                        + quiet(TAIL_OUT_SECONDS))
