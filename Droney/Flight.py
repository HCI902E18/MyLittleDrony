from threading import Thread

from bebop import Vector
from log import Logging


class Flight(Logging):
    def __init__(self, bebop):
        Logging.__init__(self)

        self.running = True

        self._tick_rate = 0.1

        self.thread = None

        self.bebop = bebop
        self._movement_vector = Vector()

    def tick(self):
        null_vector = Vector()

        self.log.info("Starting tick thread")

        while self.running:
            try:
                if not self._movement_vector.compare(null_vector):
                    self.bebop.fly(self._movement_vector)
                self.bebop.smart_sleep(self._tick_rate)

            except Exception as e:
                self.log.error("ERROR DURING FLIGHT")
                self.log.error(str(e))
        self.log.info("Killing tick thread")

    def start(self):
        # ACT LIKE THREAD
        return

    def fly(self, bebop, movement_vector):
        self.bebop = bebop
        self._movement_vector = movement_vector

        self.log.info("GETTING NEW THREAD")

        self.thread = self.__get_thread()
        self.thread.start()

    def join(self):

        self.running = False

        if self.thread is not None:
            self.thread.join()

    def __get_thread(self):
        self.running = True
        return Thread(target=self.tick, args=(()))
