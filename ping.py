from easytello import tello
import time

my_drone = tello.Tello()

# my_drone.takeoff()

# for i in range(4):
# 	my_drone.forward(100)
# 	my_drone.cw(90)

# time.sleep(5)



# my_drone.land()

# Turning on stream
# my_drone.streamon()
# Turning off stream
# my_drone.streamoff()
while True:
    batt = my_drone.get_battery()
    print(batt)
    time.sleep(5)


# time.sleep(50)
