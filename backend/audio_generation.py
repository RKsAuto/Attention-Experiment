import os
import subprocess
import sys
import wave

# Words per minute. The engines run near 200 on their own, which is too quick
# to shadow: the listener falls behind and stops tracking either ear. This is a
# dial rather than an exact figure, and each voice reads it slightly
# differently, so 100 lands at about 114 wpm with the default voice.
SPEECH_RATE = int(os.environ.get("SPEECH_RATE", 140))

# Which espeak-ng voice to speak with, on linux. mb-us1 is the mbrola american
# female, which is a good deal less buzzy than plain espeak but needs the
# mbrola packages. `espeak-ng --voices` lists the alternatives.
VOICE = os.environ.get("VOICE", "mb-us1")

# Always present, so it is what we drop back to if VOICE cannot be spoken
FALLBACK_VOICE = "en-us"


# A little silence at each end, because playback tends to clip the very start
# and the very finish, and a one syllable word there is easily lost to it
LEAD_IN_SECONDS = 0.3
TAIL_OUT_SECONDS = 0.3


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

    # a moment of quiet at each end, so the browser clips silence, not words
    quiet = lambda seconds: b"\x00" * (int(params.framerate * seconds) * width * 2)

    with wave.open(out_path, "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(width)
        out.setframerate(params.framerate)
        out.writeframes(quiet(LEAD_IN_SECONDS) + bytes(frames)
                        + quiet(TAIL_OUT_SECONDS))
