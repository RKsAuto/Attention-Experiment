import os
import subprocess
import sys
import wave

# Words per minute. Both engines run near 200 by default, which is too quick
# to shadow: the listener falls behind and stops tracking either ear.
SPEECH_RATE = int(os.environ.get("SPEECH_RATE", 110))

# Which espeak-ng voice to speak with, on linux. Handy ones: en-us, en-gb-x-rp
# (softer british), en-us+f3 (female), or mb-us1 if the mbrola packages are
# installed, which sounds a good deal less buzzy than plain espeak.
VOICE = os.environ.get("VOICE", "en-us")


def reverse_words(text):
    return " ".join(reversed(text.split()))


def text_to_wav(text, path):
    """Speak the text into a mono wav file, fully offline."""
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
        # cannot run past the command line length limit
        subprocess.run(
            ["espeak-ng", "--stdin", "-v", VOICE,
             "-s", str(SPEECH_RATE), "-w", path],
            input=text.encode(),
            check=True,
        )


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

    with wave.open(out_path, "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(width)
        out.setframerate(params.framerate)
        out.writeframes(bytes(frames))
