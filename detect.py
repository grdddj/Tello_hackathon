import numpy as np
import torch
from PIL import Image
from torch.autograd import Variable

from models import Darknet
from utils import non_max_suppression


def load_classes(path):
    """
    Loads class labels at 'path'
    """
    fp = open(path, "r")
    names = fp.read().split("\n")[:-1]
    return names


def read_image_as_numpy(filename):
    im = Image.open(filename)
    np_im = im.resize((416, 416), Image.BICUBIC)
    np_im = np.swapaxes(np.swapaxes(np_im, 0, 2), 1, 2)
    return np_im.astype(np.float32) / 255.0


def detect_image_objects(image):
    Tensor = torch.cuda.FloatTensor if torch.cuda.is_available() else torch.FloatTensor
    torch_image = torch.from_numpy(image)
    torch_image = Variable(torch_image.type(Tensor))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    classes = load_classes("data/coco.names")
    model = Darknet("data/yolov3.cfg", img_size=416).to(device)
    model.load_darknet_weights("data/yolov3.weights")

    # Get detections
    with torch.no_grad():
        detections = model(torch_image)
        detections = non_max_suppression(detections, 0.8, 0.4)

    if len(detections) == 0 or detections[0] is None:
        return []

    results = []
    for d in detections[0]:
        results.append(
            {'name': classes[int(d[6])], 'conf': float(d[5]),
             'x1': int(d[0]), 'y1': int(d[1]), 'x2': int(d[2]), 'y2': int(d[3])}
            )

    return results


def detect_image_from_path(filename):
    img = read_image_as_numpy(filename)
    img = np.expand_dims(img, axis=0)
    return detect_image_objects(img)


if __name__ == "__main__":
    print(detect_image_from_path('samples/jirka.jpg'))
