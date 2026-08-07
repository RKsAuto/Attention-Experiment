import os
import subprocess
import sys
import wave

# Words per minute. Both engines run near 175-200 by default, which is too
# quick to shadow: the listener falls behind and stops tracking either ear.
# Ordinary conversation sits around 150, and slower still is easier to follow.
# Set the SPEECH_RATE env var to retune without touching the code.
SPEECH_RATE = int(os.environ.get("SPEECH_RATE", 140))


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
        import pyttsx3  # offline too: espeak on linux, sapi on windows

        engine = pyttsx3.init()
        engine.setProperty("rate", SPEECH_RATE)
        engine.save_to_file(text, path)
        engine.runAndWait()


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
