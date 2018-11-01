class DummySensors(object):
    def __init__(self):
        self.sensors_dict = {}
        return

    def set(self, key, val):
        self.sensors_dict[key] = val
        setattr(self, key, val)
