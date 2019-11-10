from detect import detect_image_from_path

import numpy as np

SCREEN_WIDTH = 416
SCREEN_HEIGHT = 416


def get_distance_from_center(x, y):
    """
    Calculates distance of the center of an object to the centre of the screen
    """

    return np.sqrt((np.square(np.array([x, y]) - np.array([SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2]))).sum())


def analyze_scene(box):
    center_x, center_y = calc_object_center(box)
    area = calc_object_area(box)

    angle = 0
    forward = 0
    height = 0

    # our subject is too much to the right or left
    if center_x > (SCREEN_WIDTH / 2 * 1.3):
        angle = 20
    if center_x < (SCREEN_WIDTH / 2 * 0.7):
        angle = -20

    # if our subject is very low, go down a little
    #if angle == 0 and center_y > (SCREEN_HEIGHT / 2 * 1.5):
    #    height = -20

    # if not spinning, go forward towards the object
    if angle == 0 and height == 0 and area < 200 * 200:
        forward = 20

    return angle, height, forward


def calc_object_center(box):
    center_x = int((box['x2'] - box['x1']) / 2) + box['x1']
    center_y = int((box['y2'] - box['y1']) / 2) + box['y1']

    return center_x, center_y


def calc_object_area(box):
    return (box['x2'] - box['x1']) * (box['y2'] - box['y1'])


"""
def take_action_from_scene(box, actions):
    center_x, center_y = calc_object_center(box)
    area_p = calc_object_area(box)
    done = bool(get_distance_from_center(center_x, center_y) < 100 and (1500 < area_p < 5000))

    # If not done keep setting speeds
    if not done:
        angle = -int(actions[0])
        height = int(actions[1])
        if area_p < 2500:
            forward = 60
        elif area_p > 5000:
            forward = -60
        else:
            forward = 0
    else:
        angle = 0
        height = 0
        forward = 0

    return angle, height, forward
"""


def take_three_flips():
    pass  # Not yet implemented


if __name__ == "__main__":
    detections = detect_image_from_path('samples/jirka.jpg')
    found_mode = False
    is_lost = False

    for i, d in enumerate(detections):
        if d['name'] != 'person':
            continue

        found_mode = True

        angle, height, forward = analyze_scene(d)
        no_change = angle == 0 and height == 0 and forward == 0
        print("Person {}: angle {} height {} forward {}".format(i, angle, height, forward))

        if found_mode and (is_lost or no_change):
            take_three_flips()
            found_mode = False
