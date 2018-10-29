import socket
import time
from time import sleep

from pyparrot.networking.wifiConnection import WifiConnection as BaseWifiConnection


class WifiConnection(BaseWifiConnection):
    def __init__(self, drone, drone_type="Bebop2"):
        super().__init__(drone, drone_type)

        self.timeout_count = 0
        self.reconnect_sleep = 5

    def _listen_socket(self):
        data = None
        while self.is_listening:
            try:
                (data, address) = self.udp_receive_sock.recvfrom(66000)
                self.timeout_count = 0
            except socket.timeout:
                self.handle_timeout()
            except Exception as e:
                print("ERROR!: ", str(e))

            self.handle_data(data)
        self.disconnect()

    def handle_timeout(self):
        if self.timeout_count < 2:
            print("TIMEOUT")
            self.timeout_count += 1
            return

        # We need to disconnect so we do not get socket errors
        self.disconnect()

        # Store current timestamp
        now_ = time.time()

        # So we can "forcefully" reconnect to the drone
        # for 10 minutes
        while (time.time() - now_) <= 600:
            # Try and reconnect
            try:
                print(self.connect(5))

                # Try and reconnect
                if self.connect(5):
                    print("KILL IT WITH FIRE!!!")
                    # If connected, emergency land
                    if self.drone.sensors.flying_state != 'landed' and self.drone.sensors.flying_state != 'unknown':
                        if self.drone.emergency_land():
                            self.is_listening = False
                            self.disconnect()
                            return
                    else:
                        self.is_listening = False
                        self.disconnect()
                        return

                        # Handle connection errors
            except (ConnectionAbortedError, OSError):
                # Wait for a duration
                print(f"Retrying in {self.reconnect_sleep} sec")
                sleep(self.reconnect_sleep)
