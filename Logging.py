import logging
from logging import getLogger


class Logging(object):
    def __init__(self):
        name = self.__class__.__name__

        logging.basicConfig(
            format='[%(name)s][%(levelname)s]: %(message)s'
        )

        self.l = getLogger(name)
        self.l.setLevel(logging.DEBUG)

    def log_debug(self, msg):
        return self.l.debug(msg)

    def log_info(self, msg):
        return self.l.info(msg)

    def log_warn(self, msg):
        return self.l.warning(msg)

    def log_error(self, msg):
        return self.l.error(msg)
