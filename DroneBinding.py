import glob
import json
import logging
import os
import sys as system
from logging import getLogger

from inputz import Devices
from inputz.exceptions.ControllerNotFound import ControllerNotFound

from Droney.Flight import Flight
from Droney.Voice import Voice
from bebop import Bebop, Vector
from log import Logging


class DroneBinding(Logging):
    def __init__(self):
        super().__init__()

        # Dronen skal være en tråd, så de ikke hænger i beregninger til reporter
        self.bebop = Bebop()

        self.yaw_altitude_damper = 0.30

        self._movement_vector = Vector()

        self.voice = Voice()
        self.flight = Flight(self.bebop)

        self.threads = [
            self.voice,
            self.flight
        ]

        try:
            self.device = Devices().get_device()
        except ControllerNotFound:
            self.voice.force_pronounce('Unable to connect to controller.')
            exit(0)

        self.device.method_listener(self.take_off_landing, 'START')

        self.device.method_listener(self.pitch, 'LEFT_STICK')
        self.device.method_listener(self.roll, 'LEFT_STICK')

        self.device.method_listener(self.yaw, 'RIGHT_STICK')
        self.device.method_listener(self.altitude, 'RIGHT_STICK')

        self.device.method_listener(self.left_bumper, 'LEFT_BUMPER')
        self.device.method_listener(self.right_bumper, 'RIGHT_BUMPER')

        self.device.method_listener(self.change_profile, 'SELECT', self.device.Handler.single)
        self.device.method_listener(self.do_flat_trim, 'A', self.device.Handler.single)
        self.device.method_listener(self.change_geofence, 'Y', self.device.Handler.single)

        self.device.abort_function(self.abort)

        self.default_profile = 'Default'
        self.profiles = []
        self.profile_idx = 0

        self.load_profiles()
        self.profile_idx = self.get_default_profile()

        self.running = True

        self.debug = False
        self.debug_count = 0
        self.debug_button = False

        self.block_print()

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
                return idx
        return 0

    def load_profile(self, idx):
        profile = self.profiles[idx]
        self.log.info(f"Loading profile: {profile.get('name')}")

        for k, v in profile.items():
            if k[0:3] == 'max':
                self.bebop.set_setting(k, v)

        return profile.get('name')

    def start(self):
        try:
            if self.bebop.connect(5):
                self.bebop.ask_for_state_update()

                self.voice.force_pronounce("Successfully connected to the drone")

                self.device.start()

                for thread in self.threads:
                    thread.start()

                getLogger('XboxController').setLevel(logging.INFO)
                getLogger('XboxEliteController').setLevel(logging.INFO)
            else:
                self.voice.force_pronounce("Could not connect to drone")
                self.log.error("Could not connect to drone")
                exit(1)
        except ConnectionRefusedError:
            self.voice.force_pronounce("The drone did actively refuse the connection")
            self.log.error("The drone did actively refuse the connection")
            exit(1)

    def take_off_landing(self, args):
        if args and self.bebop.is_landed():
            self.voice.pronounce('Take off sequence has been initiated.')

            self.flight.fly(self.bebop, self._movement_vector)

            self.bebop.safe_takeoff(5)

        elif args and self.bebop.is_flying():
            self.voice.pronounce('Landing sequence has been initiated.')

            self._movement_vector.reset()

            self.flight.join()

            self.bebop.safe_land(5)
            # self.bebop.force_state_update(self.bebop.states.landed)

    def pitch(self, args):
        self._movement_vector.set_pitch(args[1])

    def roll(self, args):
        self._movement_vector.set_roll(args[0])

    @property
    def yaw_altitude_damper_converter(self):
        return 1 + (1 - self.yaw_altitude_damper)

    def altitude(self, args):
        yaw = abs(args[0])
        altitude = abs(args[1])

        if yaw > altitude * self.yaw_altitude_damper_converter:
            self._movement_vector.set_vertical_movement(0)
        else:
            self._movement_vector.set_vertical_movement(args[1])

    def yaw(self, args):
        yaw = abs(args[0])
        altitude = abs(args[1])

        if altitude > yaw * self.yaw_altitude_damper_converter:
            self._movement_vector.set_yaw(0)
        else:
            self._movement_vector.set_yaw(args[0])

    def do_flat_trim(self, args):
        if args and self.bebop.is_landed():
            self.voice.pronounce('Executing flat trim.')
            self.bebop.flat_trim(2)

    def change_profile(self, args):
        if args and self.bebop.is_landed():
            self.voice.pronounce(f'Loading new profile')

            self.profile_idx = (self.profile_idx + 1) % len(self.profiles)
            profile = self.load_profile(self.profile_idx)

            self.voice.pronounce(f'Changeing to profile {profile}')

    def change_geofence(self, args):
        if args:
            fence = self.bebop.toggle_fence()
            status = 'on' if fence else 'off'

            self.voice.pronounce(f'Drone geofenceing has now been turned {status}')

    def abort(self):
        self.voice.pronounce('The emergency protocol has been initiated.')
        self._movement_vector.reset()

        self.bebop.emergency_land()
        self.bebop.disconnect()

        for thread in self.threads:
            thread.join()

    def left_bumper(self, args):
        if args:
            self._movement_vector.set_yaw(-1)
        else:
            self._movement_vector.set_yaw(0)

    def right_bumper(self, args):
        if args:
            self._movement_vector.set_yaw(1)
        else:
            self._movement_vector.set_yaw(0)
