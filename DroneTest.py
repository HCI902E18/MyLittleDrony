import enum
import glob
import json
import os
import sys as system
import time
from copy import deepcopy
from threading import Thread

from inputz import Devices

from Config import c
from bebop.Bebop import Bebop
from log.LogUtils import LogUtils
from log.Logging import Logging


class DroneTest(Logging):
    def __init__(self):
        super().__init__()

        # Dronen skal være en tråd, så de ikke hænger i beregninger til reporter
        self.bebop = Bebop()

        self.max_roll = 100
        self.max_pitch = 100
        self.max_yaw = 100
        self.max_vertical_movement = 100

        self.exec_time = []
        self.logs = []
        self.func_sates = {}

        self.state = self.DroneStates.unknown

        self._tick_rate = 0.25
        self._movement_vector = {
            'roll': 0,
            'pitch': 0,
            'yaw': 0,
            'vertical_movement': 0,
        }

        self.threads = [
            Thread(name='Drone', target=self.tick, args=(())),
            Thread(name='Watchdog', target=self.watchdog, args=(()))
        ]

        self.device = Devices().get_device()

        self.device.method_listener(self.take_off, c.binding('takeoff'))
        self.device.method_listener(self.land, c.binding('landing'))
        self.device.method_listener(self.pitch, c.binding('pitch'))
        self.device.method_listener(self.roll, c.binding('roll'))
        self.device.method_listener(self.yaw, c.binding('yaw'))
        self.device.method_listener(self.altitude, c.binding('altitude_modifier'))

        self.device.method_listener(self.change_profile, c.binding('profile_change'))

        self.device.abort_function(self.abort)

        self.default_profile = 'Default'
        self.profiles = []
        self.profile_idx = 0
        self.profile_loading = False

        self.load_profiles()
        self.choose_profile()

        self.running = True

        self.i = 0

        self.block_print()

    class DroneStates(enum.Enum):
        unknown = 'unknown'
        landed = 'landed'
        takingoff = 'takingoff'
        hovering = 'hovering'
        flying = 'flying'
        landing = 'landing'
        emergency = 'emergency'
        usertakeoff = 'usertakeoff'
        motor_ramping = 'motor_ramping'
        emergency_landing = 'emergency_landing'

    @staticmethod
    def block_print():
        system.stdout = open(os.devnull, 'w')

    def load_profiles(self):
        files = glob.glob('./profiles/*.json')

        for file in files:
            with open(file, 'r') as f:
                self.profiles.append(
                    json.loads(f.read())
                )

    def choose_profile(self):
        for idx, p in enumerate(self.profiles):
            if p.get('name') == self.default_profile:
                self.profile_idx = idx

    def load_profile(self, idx):
        self.log.info(f"Loading profile: {self.profiles[idx]['name']}")
        if self.state != self.DroneStates.unknown:
            profile = self.profiles[idx]

            self.bebop.enable_geofence(True)
            self.bebop.set_max_altitude(profile.get('max_altitude'))
            self.bebop.set_max_distance(profile.get('max_distance'))
            self.bebop.set_max_tilt(profile.get('max_tilt'))
            self.bebop.set_max_tilt_rotation_speed(profile.get('max_tilt_rotation_speed'))
            self.bebop.set_max_vertical_speed(profile.get('max_vertical_speed'))
            self.bebop.set_max_rotation_speed(profile.get('max_rotation_speed'))

    def watchdog(self):
        lu = LogUtils()

        # Used for keeping the drones connection alive
        while self.running:
            self.state = self.DroneStates[self.bebop.sensors.flying_state]

            self.bebop.ask_for_state_update()
            self.bebop.smart_sleep(1)

            self.logs.append(lu.parse_sensors(self.bebop.sensors.sensors_dict))

            self.write_log()

    def tick(self):
        null_vector = deepcopy(self._movement_vector)
        while self.running:
            start_time = time.time()

            if self.state not in [self.DroneStates.flying, self.DroneStates.hovering]:
                if self._movement_vector != null_vector:
                    self.bebop.fly_direct(**self._movement_vector, duration=self._tick_rate)

            self.exec_time.append(time.time() - start_time)

    @staticmethod
    def parse(val_):
        if isinstance(val_, bytes):
            try:
                return val_.decode('utf-8')
            except Exception:
                return f"INVALID_DATA: {str(val_)}"
        return val_

    def write_log(self):
        with open('logs/exec_times.json', 'w') as f:
            f.write(json.dumps(self.exec_time, indent=4))

        with open(f'logs/flight_log.json', 'w') as f:
            f.write(json.dumps(self.logs, indent=4))

    def start(self):
        try:
            if self.bebop.connect(5):
                self.log.info("Successfully connected to the drone")

                self.device.start()

                self.load_profile(self.profile_idx)

                for thread in self.threads:
                    thread.start()
            else:
                self.log.error("Could not connect to drone")
                exit(1)
        except ConnectionRefusedError:
            self.log.error("The drone did actively refuse the connection")
            exit(1)

    def take_off(self, args):
        if args and self.state == self.DroneStates.landed:
            self.bebop.safe_takeoff(5)

    def land(self, args):
        if args and self.state in [self.DroneStates.flying, self.DroneStates.hovering]:
            self.bebop.safe_land(5)

    def pitch(self, args):
        self._movement_vector['pitch'] = self.round(args[1] * self.max_pitch)

    def roll(self, args):
        self._movement_vector['roll'] = self.round(args[0] * self.max_roll)

    def altitude(self, args):
        self._movement_vector['vertical_movement'] = self.round(args[1] * self.max_vertical_movement)

    def yaw(self, args):
        self._movement_vector['yaw'] = self.round(args[0] * self.max_yaw)

    def change_profile(self, args):
        if args and not self.profile_loading:
            self.profile_loading = True

            self.profile_idx = (self.profile_idx + 1) % len(self.profiles)
            self.load_profile(self.profile_idx)
        elif not args and self.profile_loading:
            self.profile_loading = False

        return

    @staticmethod
    def round(value):
        return int(round(value))

    def abort(self):
        for k, _ in self._movement_vector.items():
            self._movement_vector[k] = 0

        self.bebop.emergency_land()
        self.bebop.disconnect()

        self.running = False

        for thread in self.threads:
            thread.join()
