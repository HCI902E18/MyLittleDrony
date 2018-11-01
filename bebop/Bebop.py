from pyparrot.Bebop import Bebop as BaseBebop

from .WifiConnection import WifiConnection


class Bebop(BaseBebop):
    def __init__(self, drone_type="Bebop2"):
        super().__init__(drone_type=drone_type)

        self.drone_connection = WifiConnection(self, drone_type=self.drone_type)

    # def ask_for_state_update(self):
    #     return
    #     command_tuple = self.command_parser.get_command_tuple("ardrone3", "PilotingState", "moveToChanged")
    #     self.drone_connection.send_noparam_command_packet_ack(command_tuple)

