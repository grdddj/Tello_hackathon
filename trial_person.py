from easytello import tello
import time
import detect


my_drone = tello.Tello()


try:
    my_drone.streamon()

except KeyboardInterrupt as err:
    print(err)
    print("KEYBOARD INTERRUPT")
    my_drone.land()
except Exception as err:
    print("UNKNOWN ERROR")
    print(err)
    my_drone.land()

time.sleep(5000)
