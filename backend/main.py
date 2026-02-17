from fastapi import Fastapi
import pydub
@app.get("/generate")
def generate_audio(text:str):
    aud = gen_aud(text)
    aud_left = aud
    aud_right = aud
    if flipL:
        aud_left = aud.reverse()
    if flipR:
        aud_right = aud.reverse()
    return 

@app.get("/L")
def play_left():
    return

@app.get("/R")
def play_right():
    return

@app.get("/B")
def play_both():
    return