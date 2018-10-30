import logging
from logging import getLogger


class Logging(object):
    def __init__(self):
        name = self.__class__.__name__

        logging.basicConfig(
            format='[%(name)s][%(levelname)s]: %(message)s'
        )

        self.log = getLogger(name)
        self.log.setLevel(logging.DEBUG)
