import ipaddress
import json
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

        self.name = "MyLittleDroney"

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

    def _handshake(self, num_retries):
        """
        Performs the handshake over TCP to get all the connection info
        :return: True if it worked and False otherwise
        """

        # create the TCP socket for the handshake
        tcp_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        # print (self.connection_info.address, self.connection_info.port)
        # print(ipaddress.IPv4Address(self.connection_info.address))

        # connect
        # handle the broken mambo firmware by hard-coding the port and IP address
        if "Mambo" in self.drone_type:
            self.drone_ip = "192.168.99.3"
            tcp_sock.connect(("192.168.99.3", 44444))
        else:
            self.drone_ip = ipaddress.IPv4Address(self.connection_info.address).exploded
            tcp_sock.connect((self.drone_ip, self.connection_info.port))

        # send the handshake information
        if self.drone_type in ("Bebop", "Bebop2"):
            # For Bebop add video stream ports to the json request
            json_string = json.dumps({"d2c_port": self.udp_receive_port,
                                      "controller_type": self.name,
                                      "controller_name": "pyparrot",
                                      "arstream2_client_stream_port": self.stream_port,
                                      "arstream2_client_control_port": self.stream_control_port})
        else:
            json_string = json.dumps({"d2c_port": self.udp_receive_port,
                                      "controller_type": self.name,
                                      "controller_name": "pyparrot"})

        try:
            # python 3
            tcp_sock.send(bytes(json_string, 'utf-8'))
        except Exception:
            # python 2
            tcp_sock.send(json_string)

        # wait for the response
        finished = False
        num_try = 0
        while not finished and num_try < num_retries:
            data = tcp_sock.recv(4096).decode('utf-8')
            if len(data) > 0:
                my_data = data[0:-1]
                self.udp_data = json.loads(str(my_data))

                # if the drone refuses the connection, return false
                if self.udp_data['status'] != 0:
                    return False

                self.udp_send_port = self.udp_data['c2d_port']
                finished = True
            else:
                num_try += 1

        # cleanup
        tcp_sock.close()

        return finished

    def send_movement_command(self, command_tuple, roll, pitch, yaw, vertical_movement):
        self.send_single_pcmd_command(command_tuple, roll, pitch, yaw, vertical_movement)
        self.smart_sleep(0.1)
