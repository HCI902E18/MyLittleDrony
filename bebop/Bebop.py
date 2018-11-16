from copy import deepcopy

from pyparrot.Bebop import Bebop as BaseBebop

from log.Logging import Logging
from .WifiConnection import WifiConnection


class Bebop(BaseBebop, Logging):
    def __init__(self, drone_type="Bebop2"):
        super().__init__(drone_type=drone_type)
        Logging.__init__(self)

        self.fence = False
        self.last_movement = None

        self.blacklisted_movements = ['yaw', 'vertical_movement']

        self.drone_connection = WifiConnection(self, drone_type=self.drone_type)

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

    def fly(self, movement_vector, duration):
        self.last_movement = deepcopy(movement_vector)
        self.fly_direct(**movement_vector, duration=duration)

    def vector_value(self, key, value, modifier):
        if key in self.blacklisted_movements:
            return 0
        return (value * modifier) * -1

    def invert_vector(self, vector, modifier=1):
        return {k: self.vector_value(k, v, modifier) for k, v in vector.items()}

    def max_invert_vector(self, vector):
        vector_ = {}

        def vector_value(value):
            if value == 0:
                return 0
            if value > 0:
                return -100
            return 100

        for k, v in vector.items():
            if k in self.blacklisted_movements:
                vector_[k] = 0
            else:
                vector_[k] = vector_value(v)

        return vector_

    def brake1(self, duration):
        # Brake for long using inverse vector
        self.fly_direct(**self.invert_vector(self.last_movement), duration=duration)
        return True

    def brake2(self, duration):
        # Brake for medium using double inverse vector
        self.fly_direct(**self.invert_vector(self.last_movement, 2), duration=duration)
        return True

    def brake3(self, duration):
        # Brake for short using MAX inverse vector
        self.fly_direct(**self.max_invert_vector(self.last_movement), duration=duration)
        return True

    def brake4(self, duration):
        speed_x = self.sensors.sensors_dict.get('SpeedChanged_speedX')
        speed_z = self.sensors.sensors_dict.get['SpeedChanged_speedZ']
        abs_speed_x = abs(speed_x)
        abs_speed_z = abs(speed_z)
        if -0.1 <= speed_x <= 0.1 and -0.1 <= speed_z <= 0.1:
            return True
        if abs_speed_x > abs_speed_z:
            if speed_x > 0:
                self.fly_direct(roll=-10, pitch=0, yaw=0, duration=duration, vertical_movement=0)
                return False
            else:
                self.fly_direct(roll=10, pitch=0, yaw=0, duration=duration, vertical_movement=0)
                return False
        elif speed_z > 0:
            self.fly_direct(roll=0, pitch=-10, yaw=0, duration=duration, vertical_movement=0)
            return False
        else:
            self.fly_direct(roll=0, pitch=10, yaw=0, duration=duration, vertical_movement=0)
            return False
