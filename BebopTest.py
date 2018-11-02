from bebop.Bebop import Bebop

bebop = Bebop()

if bebop.connect(5):
    while True:
        bebop.test()
        print(bebop.sensors.flying_state)

        bebop.smart_sleep(1)
