import enum

from pyparrot.Bebop import Bebop as BaseBebop

from log.Logging import Logging
from .Vector import Vector
from .WifiConnection import WifiConnection


class Bebop(BaseBebop, Logging):
    def __init__(self, drone_type="Bebop2"):
        super().__init__(drone_type=drone_type)
        Logging.__init__(self)

        self.max_break_time = 1.5
        self.brake_timer = 0
        self.brake_mapping = {
            'roll': 'SpeedChanged_speedX',
            'pitch': 'SpeedChanged_speedY'
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

    def max_break_timer(self, val):
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

    def brake(self, duration):
        max_speed = self.get_max_speed()
        brake = max_speed * self.max_break_time

        if brake <= self.brake_timer:
            return True

        speed = self.sensors.sensors_dict

        movement = {movement: self.brake_value(speed.get(speed_key, 0), max_speed, movement) for movement, speed_key in
                    self.brake_mapping.items()}

        vector = Vector(**movement, duration=duration)
        self.fly_direct(**vector.emit())

        self.brake_timer += duration

        return False

    def brake_value(self, speed, max_speed, movement):
        if movement == 0:
            return 0

        movement_ = self.last_movement.get(movement)
        linear_speed = abs(max_speed) * 2
        speed_modifier = 1 if linear_speed > 1 else linear_speed

        speed = (abs(speed) / max_speed) * speed_modifier

        if movement_ > 0:
            return -speed
        return speed

    def get_max_speed(self):
        speed_keys = [k for _, k in self.brake_mapping.items()]

        return max([abs(self.sensors.sensors_dict.get(key, 0)) for key in speed_keys])
