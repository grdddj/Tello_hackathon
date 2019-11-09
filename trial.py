from easytello import tello
import time

my_drone = tello.Tello()


try:
    my_drone.streamon()

    time.sleep(1)

    my_drone.takeoff()



    for i in range(4):

        my_drone.forward(50)
        time.sleep(1)
        my_drone.back(50)
        time.sleep(1)

        # my_drone.forward(50)
        # time.sleep(1)
        # my_drone.cw(90)
        # time.sleep(1)


    # time.sleep(5)



    my_drone.land()

    # Turning on stream
    # Turning off stream
    my_drone.streamoff()

except KeyboardInterrupt as err:
    print(err)
    print("KEYBOARD INTERRUPT")
    my_drone.land()
except Error as err:
    print("UNKNOWN ERROR")
    print(err)
    my_drone.land()
