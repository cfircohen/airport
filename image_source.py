#
# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
