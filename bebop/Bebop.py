from pyparrot.Bebop import Bebop as BaseBebop

from .WifiConnection import WifiConnection


class Bebop(BaseBebop):
    def __init__(self, drone_type="Bebop2"):
        super().__init__(drone_type=drone_type)

        self.drone_connection = WifiConnection(self, drone_type=self.drone_type)
