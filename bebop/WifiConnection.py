import socket
import time
from time import sleep

from pyparrot.networking.wifiConnection import WifiConnection as BaseWifiConnection

from log.Logging import Logging


class WifiConnection(BaseWifiConnection, Logging):
    def __init__(self, drone, drone_type="Bebop2"):
        super().__init__(drone, drone_type)
        Logging.__init__(self)

        self.timeout_count = 0
        self.timeout_max = 2
        self.reconnect_sleep = 5

        self.name = "pyFlight"

    def _listen_socket(self):
        data = None
        while self.is_listening:
            try:
                (data, address) = self.udp_receive_sock.recvfrom(66000)
                self.timeout_count = 0
            except socket.timeout:
                self.handle_timeout()
            except Exception as e:
                self.log.error(f"ERROR!: {str(e)}")

            self.handle_data(data)
        self.disconnect()

    def handle_timeout(self):
        if self.timeout_count < self.timeout_max:
            self.log.debug("TIMEOUT")
            self.timeout_count += 1
            return

        # TODO: FIX
        # PlayAudio().pronounce('Initiating emergency connection protocol.')

        # We need to disconnect so we do not get socket errors
        self.disconnect()

        # Store current timestamp
        now_ = time.time()

        # So we can "forcefully" reconnect to the drone
        # for 10 minutes
        while (time.time() - now_) <= 600:
            # Try and reconnect
            try:
                # Try and reconnect
                if self.connect(5):
                    # If connected, emergency land
                    if self.drone.sensors.flying_state not in ['landed', 'unknown']:
                        self.drone.emergency_land()
                    else:
                        self.is_listening = False
                        self.disconnect()
                        return

                        # Handle connection errors
            except (ConnectionAbortedError, OSError):
                # Wait for a duration
                self.log.warning(f"Retrying in {self.reconnect_sleep} sec")
                sleep(self.reconnect_sleep)

    def send_movement_command(self, command_tuple, roll, pitch, yaw, vertical_movement):
        self.send_single_pcmd_command(command_tuple, roll, pitch, yaw, vertical_movement)
        self.smart_sleep(0.1)
