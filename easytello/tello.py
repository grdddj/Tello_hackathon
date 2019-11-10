import socket
import threading
import time
import cv2
from easytello.stats import Stats
from functools import wraps
from playsound import playsound

import detect
import navigate

class Tello:
    def __init__(self, tello_ip: str='192.168.10.1', debug: bool=True):
        # Opening local UDP port on 8889 for Tello communication
        self.local_ip = ''
        self.local_port = 8889
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.local_ip, self.local_port))

        # Setting Tello ip and port info
        self.tello_ip = tello_ip
        self.tello_port = 8889
        self.tello_address = (self.tello_ip, self.tello_port)
        self.log = []

        # Intializing response thread
        self.receive_thread = threading.Thread(target=self._receive_thread)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        # easyTello runtime options
        self.stream_state = False
        self.MAX_TIME_OUT = 15.0
        self.debug = debug
        # Setting Tello to command mode
        self.command()

        # When set to True, the photo will be saved and model will be notified
        self.send_photo = False

        # Storing the whole history of positions
        self.up_down = [0]
        self.forward_backward = [0]
        self.right_left = [0]
        self.clockwise_angle = [0]

        # Storing the histoyry of commands with their values
        self.command_history = []

        # Storing the things that can be seen from certain coordinates
        self.objects_to_be_seen = {}

        # Sending infinite ping to the battery, to keep the connection keep_alive_thread        # Intializing response thread
        self.receive_thread = threading.Thread(target=self.battery_ping)
        self.receive_thread.daemon = True
        self.receive_thread.start()

    def battery_ping(self, debug=False):
        # _f = str(inspect.stack()[0][3])

        while True:
            time.sleep(5)
            # if debug:
            #     print(f"{_f}: sent ping")
            # if command(b'battery?', debug=debug) is not None:
            #     break
            print("contacting battery")
            self.get_battery()

    # trying to apply a decorator, but solved by calling signal_to_make_photo at the end
    # @make_photo
    def send_command(self, command: str, query: bool=False, make_photo: bool=False):
        # New log entry created for the outbound command
        self.log.append(Stats(command, len(self.log)))

        # Sending command to Tello
        self.socket.sendto(command.encode('utf-8'), self.tello_address)
        # Displaying conformation message (if 'debug' os True)
        if self.debug is True:
            print('Sending command: {}'.format(command))

        # Checking whether the command has timed out or not (based on value in 'MAX_TIME_OUT')
        start = time.time()
        while not self.log[-1].got_response():  # Runs while no repsonse has been received in log
            now = time.time()
            difference = now - start
            if difference > self.MAX_TIME_OUT:
                print('Connection timed out!')
                break
        # Prints out Tello response (if 'debug' is True)
        if self.debug is True and query is False:
            print('Response: {}'.format(self.log[-1].get_response()))

        # At the end of each command, wait a little bit and take a photo
        # TODO: decide, whether time.sleep() is even necessary
        if make_photo:
            time.sleep(1)
            self.signal_to_make_photo()

    def _receive_thread(self):
        while True:
            # Checking for Tello response, throws socket error
            try:
                self.response, ip = self.socket.recvfrom(1024)
                self.log[-1].add_response(self.response)
            except socket.error as exc:
                print('Socket error: {}'.format(exc))

    def _video_thread(self):
        # Creating stream capture object
        cap = cv2.VideoCapture('udp://'+self.tello_ip+':11111')
        # Runs while 'stream_state' is True
        while self.stream_state:
            try:
                ret, frame = cap.read()
                cv2.imshow('DJI Tello', frame)

                # Video Stream is closed if escape key is pressed
                k = cv2.waitKey(1) & 0xFF
                if k == 27:
                    break

                # Used for testing purposes when in person mode
                if k == 13: # key "enter"
                    print("Enter pressed")
                    self.signal_to_make_photo()

                # Ready to respond for the need of photo
                if self.send_photo:
                    self.send_photo = False
                    print("Automatic photo")
                    file_name = self.save_photo(frame)
                    is_there_a_bottle = self.contact_model(file_name)
            except cv2.error as err:
                print("CV ERROR ENCOUNTERED")
                print(err)

        cap.release()
        cv2.destroyAllWindows()

    # Decorators are not possible to make in classes (or nor very useful)
    # Theoretically I can call self.make_photo(original_function), instead of decorating it
    def make_photo(self, orig_func):
        @wraps(orig_func)
        def wrapper(*args, **kwargs):
            result = orig_func(*args, **kwargs)

            time.sleep(1)

            self.signal_to_make_photo()

            return result

        return wrapper

    def signal_to_make_photo(self):
        """
        Sends signal to save a photo
        """
        print_with_time("signal_to_make_photo")
        self.send_photo = True

    def save_photo(self, frame):
        """
        Saves a photo on the harddrive
        """
        print_with_time("save_photo")
        timestamp = time.time()
        file_name = "photo_{}.png".format(timestamp)
        cv2.imwrite(file_name, frame)

        return file_name

    def contact_model(self, file_name):
        """
        Calls the model to analyze the photo. Stores the objects it finds in a
            local dictionary.
        Returns a boolean whether the bottle was located
        """
        print_with_time("contact_model")
        response = detect.detect_image_from_path(file_name)
        current_positon = self.get_current_position_string()
        self.objects_to_be_seen[current_positon] = response

        is_there_a_bottle = False
        for obj in response:
            if obj["name"] == "bottle":
                is_there_a_bottle = True
                print("BOTTLE THERE!")
                playsound('Hlas 001.mp3')
                break
        print("is_there_a_bottle", is_there_a_bottle)

        if is_there_a_bottle:
            for obj in response:
                if obj["name"] == "person":
                    is_there_a_bottle = True
                    print("ALCOHOLIC THERE!")
                    playsound('Hlas 003.mp3')
                    break

        # Drawing a rectangle around the object
        img = cv2.imread(file_name)
        x_pixels_dron = 960
        y_pixels_dron = 720
        x_pixels_model = 416
        y_pixels_model = 416
        x_ratio = x_pixels_dron / x_pixels_model
        y_ratio = y_pixels_dron / y_pixels_model

        found_mode = False
        is_lost = False

        for i, d in enumerate(response):
            found_mode = True

            angle, height, forward = navigate.analyze_scene(d)
            no_change = angle == 0 and height == 0 and forward == 0
            print("{} {}: angle {} height {} forward {}".format(d['name'], i, angle, height, forward))

            if found_mode and (is_lost or no_change):
                navigate.take_three_flips()
                found_mode = False        # Initializing agent to help us navigate

        print("rectangle")
        for obj in response:
            print(obj)

            x1 = int(obj["x1"] * x_ratio)
            x2 = int(obj["x2"] * x_ratio)
            y1 = int(obj["y1"] * y_ratio)
            y2 = int(obj["y2"] * y_ratio)

            area = abs(x1 - x2) * abs(y1 - y2)
            print(area)

            start = (x1, y1)
            end = (x2, y2)
            print("start", start)
            print("end", end)

            # Green colour by default
            colour = (0, 255, 0)

            # Red colour, if the object is
            # WARNING: for some reason it is not RGB, but BGR
            if obj["name"] == "bottle":
                colour = (0, 0, 255)
            # Let laptop be BLUE
            elif obj["name"] == "laptop":
                colour = (255, 0, 0)

            cv2.rectangle(img, start, end, colour, 3)

        cv2.imwrite(file_name[:-4] + "_rectangled.png", img)

        print(response)

        return is_there_a_bottle

    def wait(self, delay: float):
        # Displaying wait message (if 'debug' is True)
        if self.debug is True:
            print('Waiting {} seconds...'.format(delay))
        # Log entry for delay added
        self.log.append(Stats('wait', len(self.log)))
        # Delay is activated
        time.sleep(delay)

    def get_log(self):
        return self.log

    # Controll Commands
    def command(self):
        self.send_command('command')

    def takeoff(self):
        self.send_command('takeoff')

    def land(self):
        self.send_command('land')

    def streamon(self):
        self.send_command('streamon')
        self.stream_state = True
        self.video_thread = threading.Thread(target=self._video_thread)
        self.video_thread.daemon = True
        self.video_thread.start()

    def streamoff(self):
        self.stream_state = False
        self.send_command('streamoff')

    def emergency(self):
        self.send_command('emergency')

    # Movement Commands
    def up(self, dist: int):
        self.store_new_position("up_down", dist)
        self.send_command('up {}'.format(dist), make_photo=True)

    def down(self, dist: int):
        self.store_new_position("up_down", -dist)
        self.send_command('down {}'.format(dist), make_photo=True)

    def left(self, dist: int):
        self.store_new_position("right_left", -dist)
        self.send_command('left {}'.format(dist), make_photo=True)

    def right(self, dist: int):
        self.store_new_position("right_left", dist)
        self.send_command('right {}'.format(dist), make_photo=True)

    def forward(self, dist: int):
        self.store_new_position("forward_backward", dist)
        self.send_command('forward {}'.format(dist), make_photo=True)

    def back(self, dist: int):
        self.store_new_position("forward_backward", -dist)
        self.send_command('back {}'.format(dist), make_photo=True)

    def cw(self, degr: int):
        self.store_new_position("clockwise_angle", degr)
        self.send_command('cw {}'.format(degr), make_photo=True)

    def ccw(self, degr: int):
        self.store_new_position("clockwise_angle", -degr)
        self.send_command('ccw {}'.format(degr), make_photo=True)

    def flip(self, direc: str):
        self.send_command('flip {}'.format(direc))

    def go(self, x: int, y: int, z: int, speed: int):
        self.send_command('go {} {} {} {}'.format(x, y, z, speed))

    def curve(self, x1: int, y1: int, z1: int, x2: int, y2: int, z2: int, speed: int):
        self.send_command('curve {} {} {} {} {} {} {}'.format(x1, y1, z1, x2, y2, z2, speed))

    # Set Commands
    def set_speed(self, speed: int):
        self.send_command('speed {}'.format(speed))

    def rc_control(self, a: int, b: int, c: int, d: int):
        self.send_command('rc {} {} {} {}'.format(a, b, c, d))

    def set_wifi(self, ssid: str, passwrd: str):
        self.send_command('wifi {} {}'.format(ssid, passwrd))

    # Read Commands
    def get_speed(self):
        self.send_command('speed?', True)
        return self.log[-1].get_response()

    def get_battery(self):
        self.send_command('battery?', True)
        return self.log[-1].get_response()

    def get_time(self):
        self.send_command('time?', True)
        return self.log[-1].get_response()

    def get_height(self):
        self.send_command('height?', True)
        return self.log[-1].get_response()

    def get_temp(self):
        self.send_command('temp?', True)
        return self.log[-1].get_response()

    def get_attitude(self):
        self.send_command('attitude?', True)
        return self.log[-1].get_response()

    def get_baro(self):
        self.send_command('baro?', True)
        return self.log[-1].get_response()

    def get_acceleration(self):
        self.send_command('acceleration?', True)
        return self.log[-1].get_response()

    def get_tof(self):
        self.send_command('tof?', True)
        return self.log[-1].get_response()

    def get_wifi(self):
        self.send_command('wifi?', True)
        return self.log[-1].get_response()

    def store_new_position(self, axis, distance):
        """
        Appends current values to the history position
        """
        height_to_append = self.up_down[-1]
        length_to_append = self.forward_backward[-1]
        width_to_append = self.right_left[-1]
        angle_to_append = self.clockwise_angle[-1]

        if axis == "up_down":
            height_to_append += distance
        elif axis == "forward_backward":
            length_to_append += distance
        elif axis == "width":
            width_to_append += distance
        elif axis == "angle":
            angle_to_append += distance

        self.up_down.append(height_to_append)
        self.forward_backward.append(length_to_append)
        self.right_left.append(width_to_append)
        self.clockwise_angle.append(angle_to_append)

    def get_current_position_string(self):
        """
        Forms a string describing current position
        """
        up_down = self.up_down[-1]
        forward_backward = self.forward_backward[-1]
        right_left = self.right_left[-1]
        clockwise_angle = self.clockwise_angle[-1]

        # I chose ":" as a delimiters instead of "-", because there can be a "minus" sign in a number
        return "{}:{}:{}:{}".format(up_down, forward_backward, right_left, clockwise_angle)


def print_with_time(text):
    current_time = time.time()
    print("{} - {}".format(text, current_time))
