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

        d.method_listener(self.take_off, c.binding('takeoff'))
        d.method_listener(self.land, c.binding('landing'))
        d.method_listener(self.pitch, c.binding('pitch'))
        d.method_listener(self.roll, c.binding('roll'))
        d.method_listener(self.yaw, c.binding('yaw'))
        d.method_listener(self.altitude, c.binding('altitude_modifier'))
        d.method_listener(self.picture, c.binding('take_picture'))
        d.method_listener(self.video, [c.binding('start_video'), c.binding('stop_video')])
        d.method_listener(self.gimbal, [c.binding('gimbal_vertical'), c.binding('gimbal_horizontal')])

    class State(enum.Enum):
        deed = 'deed'
        stand_still = 'stand_still'
        takeoff = 'takeoff'
        flying = 'flying'
        landing = 'landing'

    def tick(self):
        while True:
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
        self.thread.start()
        return
        success = self.bebop.connect(10)
        if success:
            self.thread.start()

    def take_off(self, args):
        if self.state == self.State.stand_still and args:
            self.state = self.State.takeoff

            self.bebop.safe_takeoff(5)
            self.state = self.State.flying

    def land(self, args):
        if self.state == self.State.flying and args:
            self.state = self.State.landing

            self.bebop.safe_land(5)
            self.state = self.State.stand_still

    def pitch(self, args):
        self._movement_vector['pitch'] = args[1] * self.max_pitch

    def roll(self, args):
        self._movement_vector['roll'] = args[0] * self.max_roll

    def yaw(self, args):
        self._movement_vector['yaw'] = args[0] * self.max_yaw

    def altitude(self, args):
        self._movement_vector['vertical_movement'] = args[1] * self.max_vertical_movement

    def picture(self, args):
        print('picture')

    def video(self, args):
        print('video')

    def gimbal(self, args):
        print('gimbal')


if __name__ == '__main__':
    drone = DroneTest()
    drone.start()
    d.start()
