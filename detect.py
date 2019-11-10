import numpy as np
import torch
import torch.nn.functional as F
import torchvision.transforms as transforms
from PIL import Image
from torch.autograd import Variable

from models import Darknet
from utils import non_max_suppression

IMAGE_SIZE = 416


def load_classes(path):
    """
    Loads class labels at 'path'
    """
    fp = open(path, "r")
    names = fp.read().split("\n")[:-1]
    return names


def pad_to_square(img, pad_value):
    c, h, w = img.shape
    dim_diff = np.abs(h - w)
    # (upper / left) padding and (lower / right) padding
    pad1, pad2 = dim_diff // 2, dim_diff - dim_diff // 2
    # Determine padding
    pad = (0, 0, pad1, pad2) if h <= w else (pad1, pad2, 0, 0)
    # Add padding
    img = F.pad(img, pad, "constant", value=pad_value)

    return img, pad


def resize(image, size):
    image = F.interpolate(image.unsqueeze(0), size=size, mode="nearest").squeeze(0)
    return image


def read_image_as_numpy(filename):
    img = transforms.ToTensor()(Image.open(filename))
    # Pad to square resolution
    img, _ = pad_to_square(img, 0)
    # Resize
    img = resize(img, IMAGE_SIZE)

    return img

# @profile
def detect_image_objects(image):
    Tensor = torch.cuda.FloatTensor if torch.cuda.is_available() else torch.FloatTensor
    image = image.expand(1, 3, 416, 416)
    torch_image = Variable(image.type(Tensor))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(device)
    # device = "cpu"

    classes = load_classes("data/coco.names")
    model = Darknet("data/yolov3.cfg", img_size=IMAGE_SIZE).to(device)
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
    img = img.expand(1, 3, 416, 416)
    return detect_image_objects(img)


if __name__ == "__main__":
    start = time.time()
    print(detect_image_from_path('samples/jirka.jpg'))
    # print(detect_image_from_path('samples/piva.png'))
    print(time.time() - start)
