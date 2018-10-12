import enum
import glob
import json
import time
from threading import Thread

from inputz import Devices
from pyparrot.Bebop import Bebop

from Config import c


class DroneTest(object):
    def __init__(self):
        # Dronen skal være en tråd, så de ikke hænger i beregninger til reporter
        self.bebop = Bebop()

        self.max_roll = 100
        self.max_pitch = 100
        self.max_yaw = 100
        self.max_vertical_movement = 100

        self.exec_time = []
        self.logs = []

        self.state = self.State.deed
        self._tick_rate = 0.1
        self._movement_vector = {
            'roll': 0,
            'pitch': 0,
            'yaw': 0,
            'vertical_movement': 0,
        }

        self.thread = Thread(name='Drone', target=self.tick, args=(()))

        self.device = Devices().get_device()

        self.device.method_listener(self.take_off, c.binding('takeoff'))
        self.device.method_listener(self.land, c.binding('landing'))
        self.device.method_listener(self.pitch, c.binding('pitch'))
        self.device.method_listener(self.roll, c.binding('roll'))
        self.device.method_listener(self.yaw, c.binding('yaw'))
        self.device.method_listener(self.altitude, c.binding('altitude_modifier'))
        self.device.method_listener(self.picture, c.binding('take_picture'))
        self.device.method_listener(self.video, [c.binding('start_video'), c.binding('stop_video')])
        self.device.method_listener(self.gimbal, [c.binding('gimbal_vertical'), c.binding('gimbal_horizontal')])

        self.device.method_listener(self.do_flip_right, c.binding('barrel_roll_right'))
        self.device.method_listener(self.do_flip_left, c.binding('barrel_roll_left'))

        self.device.method_listener(self.change_profile, c.binding('profile_change'))

        self.default_profile = 'Default'
        self.profiles = []
        self.profile_idx = 0
        self.profile_loading = False

        self.load_profiles()
        self.choose_profile()

    class State(enum.Enum):
        deed = 'deed'
        stand_still = 'stand_still'
        takeoff = 'takeoff'
        flying = 'flying'
        landing = 'landing'

    def load_profiles(self):
        files = glob.glob('./profiles/*.json')

        for file in files:
            with open(file, 'r') as f:
                self.profiles.append(
                    json.loads(f.read())
                )
        return

    def choose_profile(self):
        for idx, p in enumerate(self.profiles):
            if p.get('name') == self.default_profile:
                self.profile_idx = idx
        return

    def load_profile(self, idx):
        print(f"Loading profile: {self.profiles[idx]['name']}")
        if self.state != self.State.deed:
            profile = self.profiles[idx]

            self.bebop.set_max_altitude(profile.get('max_altitude'))
            self.bebop.set_max_distance(profile.get('max_distance'))
            self.bebop.set_max_tilt(profile.get('max_tilt'))
            self.bebop.set_max_tilt_rotation_speed(profile.get('max_tilt_rotation_speed'))
            self.bebop.set_max_vertical_speed(profile.get('max_vertical_speed'))
            self.bebop.set_max_rotation_speed(profile.get('max_rotation_speed'))

        return

    def tick(self):
        while True:
            start_time = time.time()

            print(self.bebop.sensors.flying_state)
            if self.state == self.State.flying:
                self.bebop.fly_direct(**self._movement_vector, duration=self._tick_rate)

            sleep_time = self._tick_rate - (time.time() - start_time)

            self.log((time.time() - start_time))

            # Handle too slow calculations
            if sleep_time > 0:
                self.bebop.smart_sleep(sleep_time)
            else:
                print("ERROR TICK TO LONK")

    def log(self, exec_time):
        self.exec_time.append(exec_time)
        self.logs.append(self.bebop.sensors.sensors_dict)

    def start(self):
        self.device.start()

        success = self.bebop.connect(10)
        if success:
            # self.bebop.start_video_stream()

            self.load_profile(self.profile_idx)

            self.state = self.State.stand_still
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

            with open('exec_times.json', 'w') as f:
                f.write(json.dumps(self.exec_time))

            with open('flight_log.json', 'w') as f:
                f.write(json.dumps(self.logs))

    def pitch(self, args):
        self._movement_vector['pitch'] = int(args[1] * self.max_pitch)

    def roll(self, args):
        self._movement_vector['roll'] = int(args[0] * self.max_roll)

    def altitude(self, args):
        self._movement_vector['vertical_movement'] = int(args[1] * self.max_vertical_movement)

    def yaw(self, args):
        self._movement_vector['yaw'] = int(args[0] * self.max_yaw)

    def picture(self, args):
        print('picture')

    def video(self, args):
        print('video')

    def gimbal(self, args):
        print('gimbal')

    def do_flip_right(self, args):
        if self.state == self.State.flying and args:
            self.bebop.flip(direction="right")
            self.bebop.smart_sleep(5)

    def do_flip_left(self, args):
        if self.state == self.State.flying and args:
            self.bebop.flip(direction="left")
            self.bebop.smart_sleep(5)

    def change_profile(self, args):
        if args and not self.profile_loading:
            self.profile_loading = True

            self.profile_idx = (self.profile_idx + 1) % len(self.profiles)
            self.load_profile(self.profile_idx)
        elif not args and self.profile_loading:
            self.profile_loading = False

        return
