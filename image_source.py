import cv2
import logging
import glob
import itertools


class ImageSource(object):

  def NextFrame(self):
    raise NotImplemented


class CameraSource(ImageSource):

  def __init__(self):
    logging.info("Opening video capture")
    self.cap = cv2.VideoCapture(0)

  def NextFrame(self):
    _, frame = self.cap.read()
    return frame


class FileSource(ImageSource):

  def __init__(self, filenames):
    self.frames = [cv2.imread(f) for f in glob.glob(filenames)]
    assert self.frames, "No image files specifed"
    self.it = itertools.cycle(self.frames)

  def NextFrame(self):
    return self.it.next().copy()
