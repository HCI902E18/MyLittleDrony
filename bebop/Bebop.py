import enum
from math import floor, ceil

from pyparrot.Bebop import Bebop as BaseBebop

from bebop import Vector
from log.Logging import Logging
from .WifiConnection import WifiConnection


class Bebop(BaseBebop, Logging):
    def __init__(self, drone_type="Bebop2"):
        super().__init__(drone_type=drone_type)
        Logging.__init__(self)

        self.max_break_time = 1.5
        self.brake_timer = 0
        self.brake_mapping = {
            'roll': {
                'key': 'SpeedChanged_speedX',
                'multiplier': 1
            },
            'pitch': {
                'key': 'SpeedChanged_speedY',
                'multiplier': -1
            }
        }

        self.fence = False
        self.last_movement = None

        self.state = self.DroneStates.unknown

        self.blacklisted_movements = ['yaw', 'vertical_movement']

        self.drone_connection = WifiConnection(self, drone_type=self.drone_type)

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

    def set_setting(self, key, value):
        try:
            def func_not_found(val):
                pass

            setting = getattr(self, f'set_{key}', func_not_found)
            setting(value)
        except AttributeError:
            self.log.error(f'Unable to set set_{key}')

    def set_max_break_timer(self, val):
        self.log.info(str(val))
        self.max_break_time = val

    def toggle_fence(self):
        self.fence = not self.fence
        self.enable_geofence(self.fence)

        return self.fence

    def connect(self, num_retries):
        if super().connect(num_retries):
            self.toggle_fence()
            return True
        return False

    def fly(self, movement_vector):
        self.brake_timer = 0
        self.last_movement = movement_vector.copy()
        self.fly_direct(**movement_vector.emit())

    def update_state(self):
        self.state = self.DroneStates[self.sensors.flying_state]
        return True

    def is_flying(self):
        return self.state in [self.DroneStates.flying, self.DroneStates.hovering]

    def is_landed(self):
        return self.state in [self.DroneStates.landed, self.DroneStates.landing]

    def get_max_speed(self):
        speed_keys = [k for _, k in self.brake_mapping.items()]

        return max([abs(self.sensors.sensors_dict.get(key, 0)) for key in speed_keys])

    @staticmethod
    def round_direction(val):
        if val == 0:
            return 0
        return floor(val) if val < 0 else ceil(val)

    def speed(self, speed_value, sensor_data, max_speed):
        speed_ = sensor_data.get(speed_value.get('key'), 0)
        direction = self.round_direction(speed_)
        speed_multiplier = abs(speed_) / max_speed

        return speed_multiplier * direction

    def brake(self, duration):
        """
        SpeedChanged_speedX (float): Speed on the x axis (when drone moves forward, speed is > 0) (in %)
        SpeedChanged_speedY (float): Speed on the y axis (when drone moves to right, speed is > 0) (in %)
        """

        max_speed = self.get_max_speed()
        brake = self.max_break_time

        sensor_data = self.sensors.sensors_dict

        if brake <= self.brake_timer:
            return True

        duration_ = duration
        if (self.max_break_time - self.brake_timer) < duration:
            duration_ = self.max_break_time - self.brake_timer

        vector = Vector(duration=duration_)

        for movement, speed_value in self.brake_mapping.items():
            vector.set(
                movement,
                self.speed(speed_value, sensor_data, max_speed)
            )
        self.fly_direct(**vector.emit())

        self.brake_timer += duration
        return False
