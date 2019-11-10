import logging

from agents.drone_sim_env import drone_sim
from agents.rl_drone import RLAgent
from detect import detect_image_from_path

import numpy as np

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720


def get_distance_from_center(x, y):
    """
    Calculates distance of the center of an object to the centre of the screen
    """

    return np.sqrt((np.square(np.array([x, y]) - np.array([SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2]))).sum())


def load_agent():
    ENV_NAME = 'drone'
    env = drone_sim()
    agent = RLAgent(env)
    agent.agent.load_weights('agents/ddpg_{}_weights.h5f'.format(ENV_NAME))

    return agent


def analyze_scene(agent, box):
    center_x, center_y = calc_object_center(box)

    # pass x,y coordinate to DDPG to get actions
    actions = agent.agent.forward([center_x, center_y])

    # log debug info
    logging.debug('%d,%d,%d,%d' % (center_x, center_y, actions[0], actions[1]))

    return actions


def calc_object_center(box):
    center_x = int((box['x2'] - box['x1']) / 2) + box['x1']
    center_y = int((box['y2'] - box['y1']) / 2) + box['y1']

    return center_x, center_y


def calc_object_area(box):
    return (box['x2'] - box['x1']) * (box['y2'] - box['y1'])


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


if __name__ == "__main__":
    agent = load_agent()
    detections = detect_image_from_path('samples/bottles.jpg')
    for d in detections:
        if d['name'] != 'person':
            continue

        actions = analyze_scene(agent, d)
        take_action_from_scene(d, actions)
