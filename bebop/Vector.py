class Vector(object):
    def __init__(self, **kwargs):
        self._roll = kwargs.get('roll', 0)
        self._pitch = kwargs.get('pitch', 0)
        self._yaw = kwargs.get('yaw', 0)
        self._vertical_movement = kwargs.get('vertical_movement', 0)

        self.max_roll = 100
        self.max_pitch = 100
        self.max_yaw = 100
        self.max_vertical_movement = 100

        self.roll_damper = 0.75

        self.modifier = 1

    @staticmethod
    def round(value):
        return int(round(value, 0))

    def reset(self):
        for k, _ in self.emit().items():
            setattr(self, f'_{k}', 0)

    def set_roll(self, roll):
        self._roll = roll

    def set_pitch(self, pitch):
        self._pitch = pitch

    def set_yaw(self, yaw):
        self._yaw = yaw

    def set_vertical_movement(self, vertical_movement):
        self._vertical_movement = vertical_movement

    def emit(self):
        values = {
            'roll': self.round((self._roll * self.max_roll) * self.roll_damper * self.modifier),
            'pitch': self.round(self._pitch * self.max_pitch * self.modifier),
            'yaw': self.round(self._yaw * self.max_yaw * self.modifier),
            'vertical_movement': self.round(self._vertical_movement * self.max_vertical_movement * self.modifier)
        }

        return values

    def compare(self, vector):
        if not isinstance(vector, Vector):
            return False

        vector_values = vector.emit()
        for k, v in self.emit().items():
            if v != vector_values[k]:
                return False
        return True

    def copy(self):
        return Vector(**self.emit())

    def set(self, key, value):
        if key in self.emit():
            setattr(self, f'_{key}', value)

    def get(self, key):
        try:
            return self.emit().get(key)
        except KeyError:
            return 0

    def set_modifier(self, max_modifier):
        self.modifier = max_modifier
