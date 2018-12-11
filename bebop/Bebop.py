import enum

from pyparrot.Bebop import Bebop as BaseBebop

from log.Logging import Logging
from .WifiConnection import WifiConnection


class Bebop(BaseBebop, Logging):
    def __init__(self, drone_type="Bebop2"):
        super().__init__(drone_type=drone_type)
        Logging.__init__(self)

        self.fence = False

        self.state = self.DroneStates.unknown

        self.drone_connection = WifiConnection(self, drone_type=self.drone_type)

        self.max_modifier = 1

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
                self.log.error(f"HMM COULD NOT SET {val}")

            setting = getattr(self, f'set_{key}', func_not_found)
            setting(value)
        except AttributeError:
            self.log.error(f'Unable to set set_{key}')

    def set_max_modifier(self, val):
        self.max_modifier = val

    def toggle_fence(self):
        self.fence = not self.fence
        self.enable_geofence(self.fence)

        return self.fence

    def connect(self, num_retries):
        if super().connect(num_retries):
            self.toggle_fence()
            return True
        return False

    def update_state(self):
        self.state = self.DroneStates[self.sensors.flying_state]
        return True

    def is_flying(self):
        return self.state in [self.DroneStates.flying, self.DroneStates.hovering]

    def is_landed(self):
        return not self.is_flying()
        return self.state in [self.DroneStates.landed, self.DroneStates.landing]
