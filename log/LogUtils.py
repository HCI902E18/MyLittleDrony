from datetime import datetime


class LogUtils(object):
    def parse_sensors(self, sensor_data):
        return {
            'timestamp': datetime.now().isoformat(),
            'flyingState': sensor_data.get('FlyingStateChanged_state'),
            'alertState': sensor_data.get('AlertStateChanged_state'),
            'batteryPercent': sensor_data.get('BatteryStateChanged_battery_percent'),
            'position': {
                'latitude': self.pos_data(sensor_data.get('PositionChanged_latitude')),
                'longitude': self.pos_data(sensor_data.get('PositionChanged_longitude')),
                'altitude': self.pos_data(sensor_data.get('PositionChanged_altitude'))
            },
            'GPS': {
                'location': {
                    'latitude': self.pos_data(sensor_data.get('GpsLocationChanged_latitude')),
                    'longitude': self.pos_data(sensor_data.get('GpsLocationChanged_longitude')),
                    'altitude': self.pos_data(sensor_data.get('GpsLocationChanged_altitude'))
                },
                'accuracy': {
                    'latitude': sensor_data.get('GpsLocationChanged_latitude_accuracy'),
                    'longitude': sensor_data.get('GpsLocationChanged_longitude_accuracy'),
                    'altitude': sensor_data.get('GpsLocationChanged_altitude_accuracy')
                }
            }
        }

    @staticmethod
    def pos_data(val):
        return None if val == 500 else val
