from time import sleep

from bebop.DummySensors import DummySensors


class DummyBebop(object):
    def __init__(self):
        self.sensors = DummySensors()
        self.sensors.set('flying_state', 'landed')

    def connect(self, sleep_timer):
        return True

    def fly_direct(self, **kwargs):
        self.sensors.set('flying_state', 'flying')
        sleep(kwargs.get('duration', 1))
        self.sensors.set('flying_state', 'hovering')

    def sleep(self, secs):
        sleep(secs)

    def smart_sleep(self, sleep_timer):
        self.sleep(sleep_timer)

    def enable_geofence(self, test):
        return True

    def set_max_altitude(self, test):
        return True

    def set_max_distance(self, test):
        return True

    def set_max_tilt(self, test):
        return True

    def set_max_tilt_rotation_speed(self, test):
        return True

    def set_max_vertical_speed(self, test):
        return True

    def set_max_rotation_speed(self, test):
        return True

    def emergency_land(self):
        self.sensors.set('flying_state', 'emergency_landing')
        self.sleep(2)
        self.sensors.set('flying_state', 'landed')

    def disconnect(self):
        return

    def safe_land(self, sleep_timer):
        self.sensors.set('flying_state', 'landing')
        self.sleep(0.5)
        self.sensors.set('flying_state', 'landed')

    def safe_takeoff(self, sleep_timer):
        self.sleep(0.5)
        self.sensors.set('flying_state', 'hovering')

    def ask_for_state_update(self):
        self.sleep(2)
