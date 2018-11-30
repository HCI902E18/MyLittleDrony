import glob
import json
import logging
import os
import sys as system
import time
import traceback
import uuid
from datetime import datetime
from logging import getLogger
from threading import Thread

from inputz import Devices
from inputz.exceptions.ControllerNotFound import ControllerNotFound

from Config import c
from Voice import Voice
from bebop import Bebop, Vector
from log import LogUtils, Logging


class DroneBinding(Logging):
    def __init__(self):
        super().__init__()

        # Dronen skal være en tråd, så de ikke hænger i beregninger til reporter
        self.bebop = Bebop()
        self.bebop.set_user_sensor_callback(self.logging, ())
        self.logging_time = 0

        self.log_time = datetime.now()
        self.exec_time = []
        self.logs = []
        self.log_interval = 0.5

        self.yaw_altitude_damper = 0.30

        self.last_sate = None

        self._tick_rate = 0.15
        self._movement_vector = Vector(duration=self._tick_rate)

        self.voice = Voice()
        self.threads = [
            Thread(name='Drone', target=self.tick, args=(())),
            self.voice
        ]

        try:
            self.device = Devices().get_device()
        except ControllerNotFound:
            self.voice.pronounce('Unable to connect to controller.')
            exit(0)

        self.device.method_listener(self.take_off_landing, c.binding('takeoff_landing'))
        self.device.method_listener(self.pitch, c.binding('pitch'))
        self.device.method_listener(self.roll, c.binding('roll'))
        self.device.method_listener(self.yaw, c.binding('yaw'))
        self.device.method_listener(self.altitude, c.binding('altitude_modifier'))

        self.device.method_listener(self.change_profile, c.binding('profile_change'))
        self.device.method_listener(self.change_geofence, c.binding('change_geofence'))
        self.device.method_listener(self.do_flat_trim, c.binding('do_flat_trim'))

        self.device.method_listener(self.debug_enabler, c.binding('debug_enabler'))

        self.device.abort_function(self.abort)

        self.default_profile = 'Default'
        self.profiles = []
        self.profile_idx = 0
        self.profile_loading = False
        self.geofence_loading = False
        self.doing_flat_trim = False

        self.load_profiles()
        self.get_default_profile()

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
                self.profile_idx = idx
                return
        self.profile_idx = 0
        return

    def load_profile(self, idx):
        profile = self.profiles[idx]
        self.log.info(f"Loading profile: {profile.get('name')}")

        for k, v in profile.items():
            if k[0:3] == 'max':
                self.bebop.set_setting(k, v)

        return profile.get('name')

    def logging(self, _):
        self.bebop.update_state()

        if self.last_sate != self.bebop.state:
            self.log.debug(f"State update: {self.bebop.state}")
            self.last_sate = self.bebop.state

        if time.time() - self.logging_time < self.log_interval:
            return

        self.logging_time = time.time()

        lu = LogUtils()
        self.logs.append(lu.parse_sensors(self.bebop.sensors.sensors_dict))

        self.write_log()

    def tick(self):
        null_vector = Vector(duration=self._tick_rate)
        stopped = True

        while self.running:
            try:
                start_time = time.time()

                if self.bebop.is_flying():
                    if self._movement_vector.compare(null_vector):
                        if stopped:
                            self.bebop.smart_sleep(self._tick_rate)
                        else:
                            self.bebop.fly_direct(**null_vector.emit())
                            stopped = True
                    else:
                        self.bebop.fly_direct(**self._movement_vector.emit())
                        stopped = False

                exec_time = time.time() - start_time
                if self.bebop.is_flying() and exec_time > 0:
                    self.exec_time.append(exec_time)
            except Exception as e:
                folder = 'crashes/'
                file = f'{uuid.uuid4().hex}.txt'
                os.makedirs(folder, exist_ok=True)

                with open(f'{folder}/{file}', 'w') as f:
                    f.write(f'{str(e)}\n')
                    f.write(traceback.format_exc() + '\n')

    def write_log(self):
        try:
            log_date_format = self.log_time.strftime('[%d-%m-%Y][%H.%M.%S]')

            os.makedirs(f'logs/{log_date_format}', exist_ok=True)

            with open(f'logs/{log_date_format}/exec_times.json', 'w') as f:
                f.write(json.dumps(self.exec_time, indent=4))

            with open(f'logs/{log_date_format}/flight_log.json', 'w') as f:
                f.write(json.dumps(self.logs, indent=4))
        except Exception:
            pass

    def start(self):
        try:
            if self.bebop.connect(5):
                self.bebop.ask_for_state_update()

                self.voice.force_pronounce("Successfully connected to the drone")

                self.device.start()
                getLogger('XboxController').setLevel(logging.INFO)
                getLogger('XboxEliteController').setLevel(logging.INFO)

                self.load_profile(self.profile_idx)

                for thread in self.threads:
                    thread.start()
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

            self.bebop.safe_takeoff(5)
        elif args and self.bebop.is_flying():
            self.voice.pronounce('Landing sequence has been initiated.')

            self._movement_vector.reset()

            self.bebop.safe_land(5)
            self.bebop.smart_sleep(2)
            self.bebop.ask_for_state_update()

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
        if not self.debug:
            return

        self.voice.pronounce('Executing flat trim.')

        if args and not self.doing_flat_trim:
            self.doing_flat_trim = True
            self.bebop.flat_trim(2)

        elif not args and self.doing_flat_trim:
            self.doing_flat_trim = False

    def change_profile(self, args):
        if not self.debug:
            return

        if args and not self.profile_loading:
            self.profile_loading = True

            self.profile_idx = (self.profile_idx + 1) % len(self.profiles)
            profile = self.load_profile(self.profile_idx)

            self.voice.pronounce(f'Changeing to profile {profile}')

        elif not args and self.profile_loading:
            self.profile_loading = False

        return

    def change_geofence(self, args):
        if not self.debug:
            return

        if args and not self.geofence_loading:
            self.geofence_loading = True

            fence = self.bebop.toggle_fence()
            status = 'on' if fence else 'off'

            self.voice.pronounce(f'Drone geofenceing has now been turned {status}')
        elif not args and self.geofence_loading:
            self.geofence_loading = False

    def abort(self):
        self.voice.pronounce('The emergency protocol has been initiated.')
        self._movement_vector.reset()

        self.bebop.emergency_land()
        self.bebop.disconnect()

        self.running = False

        for thread in self.threads:
            thread.join()

    def debug_enabler(self, args):
        if self.bebop.is_landed():
            if args == 1 and not self.debug_button:
                if self.debug_count == 2:
                    self.debug_count = 0
                    self.debug = not self.debug

                    state = 'enabled' if self.debug else 'disabled'
                    self.voice.pronounce(f"Debugging has been {state}")
                else:
                    self.debug_count += 1
                self.debug_button = True
            if args == 0 and self.debug_button:
                self.debug_button = False
