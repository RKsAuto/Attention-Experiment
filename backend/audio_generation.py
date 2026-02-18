
import os
class gen_aud():
    def audio_generator(self, text:str):
        os.system("say " + text)
        
        return "done playing"

if __name__ == "__main__":
    gen = gen_aud()
    aud = gen.audio_generator("I am Rish")
    print(aud)