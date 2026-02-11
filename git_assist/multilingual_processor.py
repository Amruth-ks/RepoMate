from langdetect import detect
from googletrans import Translator

class MultilingualProcessor:

    def __init__(self):
        self.translator = Translator()

    def normalize(self, text):
        try:
            lang = detect(text)
        except:
            lang = "en"

        if lang != "en":
            translated = self.translator.translate(text, dest="en")
            return translated.text, lang
        return text, "en"
