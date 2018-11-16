class Vector(object):
    def __init__(self, **kwargs):
        self._roll = kwargs.get('roll', 0)
        self._pitch = kwargs.get('pitch', 0)
        self._yaw = kwargs.get('yaw', 0)
        self._vertical_movement = kwargs.get('vertical_movement', 0)
        self._duration = kwargs.get('duration', 0)

        self.max_roll = 100
        self.max_pitch = 100
        self.max_yaw = 100
        self.max_vertical_movement = 100

        self.roll_damper = 0.75

    @staticmethod
    def round(value):
        return int(round(value))

    def reset(self):
        for k, _ in self.emit().items():
            setattr(self, f'_{k}', 0)

    def set_roll(self, roll):
        self._roll = self.round((roll * self.max_roll) * self.roll_damper)

    def set_pitch(self, pitch):
        self._pitch = self.round(pitch * self.max_pitch)

    def set_yaw(self, yaw):
        self._yaw = self.round(yaw * self.max_yaw)

    def set_vertical_movement(self, vertical_movement):
        self._vertical_movement = self.round(vertical_movement * self.max_vertical_movement)

    def set_duration(self, duration):
        self._duration = duration

    def emit(self, ignore_duration=False):
        if ignore_duration:
            return {
                'roll': self._roll,
                'pitch': self._pitch,
                'yaw': self._yaw,
                'vertical_movement': self._vertical_movement,
            }
        return {
            'roll': self._roll,
            'pitch': self._pitch,
            'yaw': self._yaw,
            'vertical_movement': self._vertical_movement,
            'duration': self._duration,
        }

    def compare(self, vector):
        if not isinstance(vector, Vector):
            return False

        vector_values = vector.emit(True)
        for k, v in self.emit(True).items():
            if v != vector_values[k]:
                return False
        return True

    def copy(self):
        return Vector(**self.emit())
