import threading
from queue import Queue
from time import sleep

import pyttsx3

from log.Logging import Logging


class Voice(threading.Thread, Logging):
    def __init__(self):
        threading.Thread.__init__(self)
        Logging.__init__(self)

        self.things_to_say = Queue()
        self.running = True

        return

    def pronounce(self, text):
        self.things_to_say.put_nowait(text)

    def force_pronounce(self, text):
        self.speak(text)

    def join(self, timeout=None):
        self.running = False

        super().join(timeout)

    @staticmethod
    def speak(text):
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

    def run(self):
        while self.running:
            if self.things_to_say.qsize() > 0:
                text = self.things_to_say.get()

                self.log.info(text)
                self.speak(text)
            else:
                sleep(1)
