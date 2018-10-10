import configparser
import os


class Config(object):
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(os.environ.get('CONFIG', 'config.ini'))

    def binding(self, key):
        if 'BINDINGS' not in self.config:
            print("ERROR BINDINGS NOT FOUND")

        return self.config['BINDINGS'].get(key)


c = Config()
