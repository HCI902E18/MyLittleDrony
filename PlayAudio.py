from threading import Thread

import pyttsx3


class PlayAudio(object):
    def pronounce(self, text):
        thread = Thread(target=self.__pronounce, args=(text,))
        thread.start()

    def __pronounce(self, text):
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
