from pyparrot.Bebop import Bebop as BaseBebop

from log.Logging import Logging
from .BebopSensors import BebopSensors
from .FlightLog import FlightLog
from .WifiConnection import WifiConnection


class Bebop(BaseBebop, Logging):
    def __init__(self, drone_type="Bebop2"):
        super().__init__(drone_type=drone_type)
        Logging.__init__(self)

        self.fence = False

        self.drone_connection = WifiConnection(self, drone_type=self.drone_type)
        self.drone_logging = FlightLog(self)
        self.sensors = BebopSensors(self.drone_logging)

    def set_setting(self, key, value):
        try:
            def func_not_found(val):
                self.log.error(f"Unable to set value: {val}")

            setting = getattr(self, f'set_{key}', func_not_found)
            setting(value)
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

    def is_flying(self):
        return not self.is_landed()
        # return self.sensors.is_landed()
        # return self.sensors.is_flying()

    def fly(self, vector):
        command_tuple = self.command_parser.get_command_tuple("ardrone3", "Piloting", "PCMD")

        my_roll = self._ensure_fly_command_in_range(vector.get('roll'))
        my_pitch = self._ensure_fly_command_in_range(vector.get('pitch'))
        my_yaw = self._ensure_fly_command_in_range(vector.get('yaw'))
        my_vertical = self._ensure_fly_command_in_range(vector.get('vertical_movement'))

        self.drone_connection.send_movement_command(command_tuple, my_roll, my_pitch, my_yaw, my_vertical)

    @property
    def states(self):
        return self.sensors.DroneStates

    def force_state_update(self, state):
        if state in self.states:
            self.log.info(f"Forcing fly state as: {state.value}")
            self.sensors.update('FlyingStateChanged_state', state.value, None)

        return
