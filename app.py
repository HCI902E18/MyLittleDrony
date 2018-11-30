from DroneBinding import DroneBinding
from Voice import Voice

v = Voice()
v.speak("Starting Drone")
drone = DroneBinding()

if __name__ == '__main__':
    drone.start()
