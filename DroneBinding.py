import enum
import glob
import json
import logging
import os
import sys as system
import time
from copy import deepcopy
from datetime import datetime
from logging import getLogger
from threading import Thread

from inputz import Devices

from Config import c
from bebop.Bebop import Bebop
from log.LogUtils import LogUtils
from log.Logging import Logging


class DroneBinding(Logging):
    def __init__(self):
        super().__init__()

        # Dronen skal være en tråd, så de ikke hænger i beregninger til reporter
        self.bebop = Bebop()
        self.bebop.set_user_sensor_callback(self.logging, ())
        self.logging_time = 0

        self.max_roll = 100
        self.max_pitch = 100
        self.max_yaw = 100
        self.max_vertical_movement = 100

        self.log_time = datetime.now()
        self.exec_time = []
        self.logs = []
        self.log_interval = 0.5

        self.state = self.DroneStates.unknown
        self.last_sate = None

        self._tick_rate = 0.15
        self._movement_vector = {
            'roll': 0,
            'pitch': 0,
            'yaw': 0,
            'vertical_movement': 0,
        }

        self.threads = [
            Thread(name='Drone', target=self.tick, args=(())),
        ]

        self.device = Devices().get_device()

        self.device.method_listener(self.take_off_landing, c.binding('takeoff'))
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
        self.get_default_profile()

        self.running = True

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

    def get_default_profile(self):
        for idx, p in enumerate(self.profiles):
            if p.get('name') == self.default_profile:
                self.profile_idx = idx
                return
        self.profile_idx = 0
        return

    def load_profile(self, idx):
        self.log.info(f"Loading profile: {self.profiles[idx]['name']}")
        profile = self.profiles[idx]

        for k, v in profile.items():
            if k[0:3] == 'max':
                self.bebop.set_setting(k, v)

    def logging(self, _):
        self.state = self.DroneStates[self.bebop.sensors.flying_state]

        if self.last_sate != self.state:
            self.log.debug(f"State update: {self.state}")
            self.last_sate = self.state

        if time.time() - self.logging_time < self.log_interval:
            return

        self.logging_time = time.time()

        lu = LogUtils()
        self.logs.append(lu.parse_sensors(self.bebop.sensors.sensors_dict))

        self.write_log()

    def tick(self):
        while self.running:
            start_time = time.time()

            if self.state in [self.DroneStates.flying, self.DroneStates.hovering]:
                self.bebop.fly_direct(**self._movement_vector, duration=self._tick_rate)

            exec_time = time.time() - start_time
            if self.state in [self.DroneStates.flying, self.DroneStates.hovering] and exec_time > 0:
                self.exec_time.append(exec_time)

    def write_log(self):
        log_date_format = self.log_time.strftime('[%d-%m-%Y][%H.%M.%S]')

        os.makedirs(f'logs/{log_date_format}', exist_ok=True)

        with open(f'logs/{log_date_format}/exec_times.json', 'w') as f:
            f.write(json.dumps(self.exec_time, indent=4))

        with open(f'logs/{log_date_format}/flight_log.json', 'w') as f:
            f.write(json.dumps(self.logs, indent=4))

    def start(self):
        try:
            if self.bebop.connect(5):
                self.log.info("Successfully connected to the drone")

                self.device.start()
                getLogger('XboxController').setLevel(logging.INFO)
                getLogger('XboxEliteController').setLevel(logging.INFO)

                self.load_profile(self.profile_idx)

                for thread in self.threads:
                    thread.start()
            else:
                self.log.error("Could not connect to drone")
                exit(1)
        except ConnectionRefusedError:
            self.log.error("The drone did actively refuse the connection")
            exit(1)

    def take_off_landing(self, args):
        if args and self.state in [self.DroneStates.landed, self.DroneStates.unknown, self.DroneStates.landing]:
            self.bebop.safe_takeoff(5)
        elif args and self.state in [self.DroneStates.flying, self.DroneStates.hovering]:
            self.reset_movement()
            self.bebop.smart_sleep(2)
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

    def reset_movement(self):
        for k, _ in self._movement_vector.items():
            self._movement_vector[k] = 0

    def abort(self):
        self.reset_movement()

        self.bebop.emergency_land()
        self.bebop.disconnect()

        self.running = False

        for thread in self.threads:
            thread.join()
