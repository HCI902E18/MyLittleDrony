import threading
from time import sleep

from bebop import Vector
from log import Logging


class Flight(threading.Thread, Logging):
    def __init__(self, bebop):
        threading.Thread.__init__(self)
        Logging.__init__(self)

        self.running = True
        self._fly = False

        self._tick_rate = 0.1

        self.bebop = bebop
        self._movement_vector = Vector()

    def run(self):
        null_vector = Vector()

        while self.running:
            if not self._fly:
                sleep(self._tick_rate)
                continue

            try:
                if not self._movement_vector.compare(null_vector):
                    self.bebop.fly(self._movement_vector)
                self.bebop.smart_sleep(self._tick_rate)

            except Exception as e:
                self.log.error("ERROR DURING FLIGHT")
                self.log.error(str(e))

    def fly(self, bebop, movement_vector):
        self.log.info("Starting tick thread")

        self.bebop = bebop
        self._movement_vector = movement_vector

        self._fly = True

    def kill(self):
        self.log.info("Killing tick thread")

        self._fly = False
        self.running = False
