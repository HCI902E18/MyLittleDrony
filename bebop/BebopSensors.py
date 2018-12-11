import enum

from pyparrot.Bebop import BebopSensors as BaseBebopSensors


class BebopSensors(BaseBebopSensors):
    def __init__(self, logger=None):
        self.state = self.DroneStates.unknown

        self.logger = logger

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

    def update(self, sensor_name, sensor_value, sensor_enum):
        super().update(sensor_name, sensor_value, sensor_enum)

        self.state = self.DroneStates[self.flying_state]

        if self.logger is not None:
            self.logger.update()

        return True

    def is_flying(self):
        return self.state in [self.DroneStates.flying, self.DroneStates.hovering]

    def is_landed(self):
        return not self.is_flying()
