from easytello import tello
import time

my_drone = tello.Tello()


try:
    my_drone.streamon()

    time.sleep(1)

    my_drone.takeoff()

    # Deleting old commands
    with open("commands.txt", "w") as command_file:
        pass

    index = 0
    while True:
        time.sleep(0.5)
        with open("commands.txt", "r") as command_file:
            lines = command_file.readlines()
            try:
                current_command_line = lines[index]
                if current_command_line:
                    index += 1
                    my_drone.send_command(current_command_line, make_photo=True)
            except IndexError:
                # print("INDEX ERRROR")
                pass

    my_drone.land()

    # Turning on stream
    # Turning off stream
    my_drone.streamoff()

except KeyboardInterrupt as err:
    print(err)
    print("KEYBOARD INTERRUPT")
    my_drone.land()
except Exception as err:
    print("UNKNOWN ERROR")
    print(err)
    my_drone.land()
