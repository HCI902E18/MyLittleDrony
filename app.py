import enum
import time
from threading import Thread

from inputz import Devices
from pyparrot.Bebop import Bebop

from Config import c

d = Devices().get_device()


class DroneTest(object):
    def __init__(self):
        # Dronen skal være en tråd, så de ikke hænger i beregninger til reporter
        self.bebop = Bebop()

        self.max_roll = 100
        self.max_pitch = 100
        self.max_yaw = 100
        self.max_vertical_movement = 100

        self.state = self.State.deed
        self._tick_rate = 0.1
        self._movement_vector = {
            'roll': 0,
            'pitch': 0,
            'yaw': 0,
            'vertical_movement': 0,
        }

        self.thread = Thread(name='Drone', target=self.tick, args=(()))

    class State(enum.Enum):
        deed = 'deed'
        stand_still = 'stand_still'
        takeoff = 'takeoff'
        flying = 'flying'
        landing = 'landing'

    def tick(self):
        while True:
            print("TICK")
            start_time = time.time()

            if self.state == self.State.flying:
                self.bebop.fly_direct(**self._movement_vector, duration=self._tick_rate)

            sleep_time = self._tick_rate - (time.time() - start_time)

            # Handle too slow calculations
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                print("ERROR TICK TO LONK")

    def start(self):
        success = self.bebop.connect(10)
        if success:
            self.thread.start()

    @d.listen(c.binding('takeoff'))
    def take_off(self, args):
        if self.state == self.State.stand_still and args:
            self.state = self.State.takeoff

            success = self.bebop.safe_takeoff(5)

            if success:
                self.state = self.State.flying
            else:
                self.state = self.State.stand_still

    @d.listen(c.binding('landing'))
    def land(self, args):
        if self.state == self.State.flying and args:
            self.state = self.State.landing

            success = self.bebop.safe_land(5)

            if success:
                self.state = self.State.stand_still
            else:
                self.state = self.State.flying

    @d.listen(c.binding('pitch'))
    def pitch(self, args):
        print('pitch')

    @d.listen(c.binding('roll'))
    def roll(self, args):
        print('roll')

    @d.listen(c.binding('yaw'))
    def yaw(self, args):
        print('yaw')

    @d.listen(c.binding('altitude_modifier'))
    def altitude(self, args):
        print('altitude')

    @d.listen(c.binding('take_picture'))
    def picture(self, args):
        print('picture')

    @d.listen(c.binding('start_video'), c.binding('stop_video'))
    def video(self, args):
        print('video')

    @d.listen(c.binding('gimbal_vertical'), c.binding('gimbal_horizontal'))
    def gimbal(self, args):
        print('gimbal')


if __name__ == '__main__':
    drone = DroneTest()

    drone.start()
    d.start(drone)
