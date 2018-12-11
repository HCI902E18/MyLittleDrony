import json
import os
import time
from datetime import datetime

from bebop.LogUtils import LogUtils


class FlightLog(object):
    def __init__(self, bebop):
        self.last_sate = None
        self.log_interval = 0.5
        self.logging_time = 0

        self.log_time = datetime.now()
        self.logs = []

        self.bebop = bebop

        self.lu = LogUtils()

    def update(self):

        if self.last_sate != self.bebop.state:
            self.last_sate = self.bebop.state

        if time.time() - self.logging_time < self.log_interval:
            return

        self.logging_time = time.time()

        self.logs.append(self.lu.parse_sensors(self.bebop.sensors.sensors_dict))

        self.write_log()

    def write_log(self):
        try:
            log_date_format = self.log_time.strftime('[%d-%m-%Y][%H.%M.%S]')

            os.makedirs(f'logs/{log_date_format}', exist_ok=True)

            with open(f'logs/{log_date_format}/flight_log.json', 'w') as f:
                f.write(json.dumps(self.logs, indent=4))
        except Exception:
            pass
