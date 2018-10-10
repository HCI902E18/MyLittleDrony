from inputz import Devices
from pyparrot.Bebop import Bebop

from Config import c

d = Devices().get_device()


class DroneTest(object):
    def __init__(self):
        self.bebop = Bebop()

    @d.listen(c.binding('takeoff'))
    def take_off(self, args):
        print('take_off')

    @d.listen(c.binding('landing'))
    def land(self, args):
        print('land')

    @d.listen(c.binding('pitch'))
    def pitch(self, args):
        print('pitch')

    @d.listen(c.binding('roll'))
    def roll(self, args):
        print('roll')

    @d.listen(c.binding('yaw'))
    def yaw(self, args):
        print('yaw')

    @d.listen(c.binding('altitude_modifier'))
    def altitude(self, args):
        print('altitude')

    @d.listen(c.binding('take_picture'))
    def picture(self, args):
        print('picture')

    @d.listen(c.binding('start_video'), c.binding('stop_video'))
    def video(self, args):
        print('video')

    @d.listen(c.binding('gimbal_vertical'), c.binding('gimbal_horizontal'))
    def gimbal(self, args):
        print('gimbal')


if __name__ == '__main__':
    drone = DroneTest()
    d.start(drone)
