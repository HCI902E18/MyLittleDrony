class Bebop(object):
    def __init__(self, drone_type="Bebop2"):
        self.drone_type = drone_type

        # self.drone_connection = WifiConnection(self, drone_type=drone_type)
        #
        # # intialize the command parser
        # self.command_parser = DroneCommandParser()
        #
        # # initialize the sensors and the parser
        # self.sensors = BebopSensors()
        # self.sensor_parser = DroneSensorParser(drone_type=drone_type)
