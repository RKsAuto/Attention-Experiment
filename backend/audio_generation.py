
from gtts import gtts
class gen_aud():
    def audio_generator(self, text:str):
        aud = gtts(text)
        
        return aud

if name == "_main_":
    gen = gen_aud()
    aud = gen_aud.audio_generator("I am Rish")