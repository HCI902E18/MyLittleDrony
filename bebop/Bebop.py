import enum

from pyparrot.Bebop import Bebop as BaseBebop

from log.Logging import Logging
from .Vector import Vector
from .WifiConnection import WifiConnection


class Bebop(BaseBebop, Logging):
    def __init__(self, drone_type="Bebop2"):
        super().__init__(drone_type=drone_type)
        Logging.__init__(self)

        self.max_break_time = 1
        self.brake_timer = 0

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
            setattr(self, f'set_{key}', value)
        except AttributeError:
            self.log.error(f'Unable to set set_{key}')

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

    def brake1(self, duration):
        speed_x = self.sensors.sensors_dict.get('SpeedChanged_speedX', 0)
        speed_z = self.sensors.sensors_dict.get('SpeedChanged_speedZ', 0)

        abs_speed_x = abs(speed_x)
        abs_speed_z = abs(speed_z)

        if -0.3 <= speed_x <= 0.3 and -0.3 <= speed_z <= 0.3:
            return True
        if abs_speed_x > abs_speed_z:
            if speed_x > 0:
                self.fly_direct(roll=-50, pitch=0, yaw=0, duration=duration, vertical_movement=0)
                return False
            else:
                self.fly_direct(roll=50, pitch=0, yaw=0, duration=duration, vertical_movement=0)
                return False
        elif speed_z > 0:
            self.fly_direct(roll=0, pitch=-50, yaw=0, duration=duration, vertical_movement=0)
            return False
        else:
            self.fly_direct(roll=0, pitch=50, yaw=0, duration=duration, vertical_movement=0)
            return False

    def brake2(self, duration):
        max_speed = self.get_max_speed()
        brake = max_speed * self.max_break_time

        brake_mapping = {
            'roll': 'SpeedChanged_speedX',
            'pitch': 'SpeedChanged_speedZ'
        }

        if brake <= self.brake_timer:
            return True

        speed = self.sensors.sensors_dict

        movement = {movement: self.brake_value(speed.get(speed_key, 0), max_speed, movement) for movement, speed_key in brake_mapping.items()}
        vector = Vector(**movement, duration=duration)
        self.fly_direct(**vector.emit())

        self.brake_timer += duration

        return False

    def brake_value(self, speed, max_speed, movement):
        if self.last_movement.get(movement) > 0:
            return -(abs(speed) / max_speed)
        elif self.last_movement.get(movement) < 0:
            return abs(speed) / max_speed
        return 0

    def get_max_speed(self):
        speed_keys = ['SpeedChanged_speedX', 'SpeedChanged_speedZ']

        return max([abs(self.sensors.sensors_dict.get(key, 0)) for key in speed_keys])
