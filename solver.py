#!/usr/local/bin/python
import sys
import os
import cv2
import numpy as np
import logging
import argparse
import traceback
import collections
import itertools
import cPickle as pickle
import operator
import copy
import glob
import time
from enum import Enum
import image_source
import board
import pieces
import solutions

MAX_PLANES = 6
Options = None

Rect = collections.namedtuple("Rect", ["x", "y", "w", "h"])
Constraint = Enum("Constraint", "VERTICAL HORIZONTAL")


def WaitKey(delay_ms=5):
  key = cv2.waitKey(delay_ms) & 0xFF
  if key == 27:
    raise Exception("Abort")
  return chr(key)


def DebugShow(image):
  global Options
  if Options.verbose:
    stack = sys._getframe(1)
    cv2.imshow("{0}:{1}".format(stack.f_code.co_name, stack.f_lineno), image)


def Crop(img, rect):
  return img[rect.y:rect.y + rect.h, rect.x:rect.x + rect.w]


def PrepareImage(image):
  """Converts color image to black and white"""
  # work on gray scale
  bw = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

  # remove noise, preserve edges
  bw = cv2.bilateralFilter(bw, 9, 75, 75)

  # binary threshold
  bw = cv2.adaptiveThreshold(bw, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                             cv2.THRESH_BINARY, 11, 2)
  return bw


def FindExternalContour(image_bw):
  """Returns the largest external contour."""
  # all external contours
  _, contours, _ = cv2.findContours(image_bw.copy(), cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
  logging.debug("found {} external contours in image".format(len(contours)))
  # max contour by area size
  largest = max(contours, key=lambda cnt: cv2.contourArea(cnt))
  return Rect(*cv2.boundingRect(largest))


def FindInternalBox(bw):
  """Finds where the puzzle card is located.

  Detects all vertical and horizontal lines, and returns the largest
  contour that bounds them"""

  # Invert colors. HoughLines searches white lines on black background
  target = 255 - bw.copy()
  DebugShow(target)

  lines = cv2.HoughLinesP(target, 1, np.pi / 180, 100, 100, 10)
  if lines is None:
    logging.debug("HoughLinesP failed")
    return None

  logging.debug("Found {} lines using HoughLinesP".format(len(lines)))

  lines_image = np.zeros_like(target)
  for line in lines:
    for x1, y1, x2, y2 in line:
      if abs(x1 - x2) < 20:
        # vertical line
        x = min(x1, x2)
        cv2.line(lines_image, (x, y1), (x, y2), 255, 0)
      if abs(y1 - y2) < 20:
        y = min(y1, y2)
        cv2.line(lines_image, (x1, y), (x2, y), 255, 0)

  kernel = np.ones((5, 5), np.uint8)
  lines_image = cv2.dilate(lines_image, kernel, iterations=2)
  DebugShow(lines_image)

  return FindExternalContour(lines_image)


def FindBoard(frame_bw):
  outer = FindExternalContour(frame_bw)
  logging.debug("Found game's outer box {0}".format(outer))

  outer_img = Crop(frame_bw, outer)
  inner = FindInternalBox(outer_img)
  if not inner or inner.w < 100 or inner.h < 100:
    logging.debug("Cound not find game's inner box")
    return None

  box = Rect(outer.x + inner.x, outer.y + inner.y, inner.w, inner.h)
  logging.debug("Found board location in frame {0}".format(box))
  return box


def ReadCells(frame, box):
  """Reads grid images from frame. Each sub image corresponds to a single cell."""
  cells = np.array([None] * 16, dtype='O').reshape(4, 4)

  cell_size = np.array([box.w / 4, box.h / 4])
  top_left_loc = np.array([box.x, box.y])

  for selected_cell in itertools.product(range(4), range(4)):
    loc = top_left_loc + np.array(selected_cell[::-1]) * cell_size
    cells[selected_cell] = Crop(frame, Rect(loc[0], loc[1], cell_size[0],
                                            cell_size[1]))

  return cells


def LoadTemplates():

  def ReadTemplates(base, value):
    filenames = os.path.join("templates",
                             "{0}_{1}*.png".format(base, value.name.lower()))
    logging.debug("Reading templates: {0}".format(glob.glob(filenames)))
    templates = [cv2.imread(f) for f in glob.glob(filenames)]
    templates = [cv2.cvtColor(t, cv2.COLOR_RGB2GRAY) for t in templates]
    return templates

  return dict([(o, ReadTemplates("obj", o))
               for o in [board.SquareType.UP, board.SquareType.RIGHT,
                         board.SquareType.DOWN, board.SquareType.LEFT,
                         board.SquareType.ANY]] + [(c, ReadTemplates("con", c))
                                                   for c in Constraint])


def MatchTemplate(template, target):
  """Returns match score for given template"""
  res = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
  min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
  return max_val


def DetectObjects(templates, cells):
  objects = np.array([None] * 16, dtype='O').reshape(4, 4)
  for selected in itertools.product(range(4), range(4)):
    target = cells[selected].copy()
    DebugShow(target)

    matches = [(o, MatchTemplate(t, target))
               for o in [board.SquareType.UP, board.SquareType.RIGHT,
                         board.SquareType.DOWN, board.SquareType.LEFT,
                         board.SquareType.ANY] for t in templates[o]]
    best = max(matches, key=operator.itemgetter(1))
    if best[1] < 0.6:
      continue

    logging.debug("Detected {0} with score {1} at {2}".format(best[0], best[1],
                                                              selected))
    objects[selected] = best[0]
  return objects


def DetectConstraints(templates, cells):
  constraints = np.array([None] * 16, dtype='O').reshape(4, 4)
  for selected in itertools.product(range(4), range(4)):
    target = cells[selected].copy()
    DebugShow(target)

    matches = [(o, MatchTemplate(t, target))
               for o in Constraint for t in templates[o]]
    best = max(matches, key=operator.itemgetter(1))
    if best[1] < 0.6:
      continue

    logging.debug("Detected {0} with score {1} at {2}".format(best[0], best[1],
                                                              selected))
    constraints[selected] = best[0]
  return constraints


def PassConstraints(constraints, solution):
  b = solutions.PlacePieces(solution)
  for selected in itertools.product(range(4), range(4)):
    loc = np.array([1, 1]) + selected
    if constraints[selected] is Constraint.VERTICAL:
      if b[zip(loc)] not in [board.SquareType.UP, board.SquareType.DOWN,
                             board.SquareType.AIR]:
        return False
    if constraints[selected] is Constraint.HORIZONTAL:
      if b[zip(loc)] not in [board.SquareType.LEFT, board.SquareType.RIGHT,
                             board.SquareType.AIR]:
        return False
  return True


def BuildPuzzleBoardFromObjects(objects):
  """Build 6x6 board and fills in the objects"""
  b = board.Empty()
  for selected in itertools.product(range(4), range(4)):
    loc = np.array([1, 1]) + selected
    if objects[selected]:
      b[zip(loc)] = objects[selected]

  return b


def LoadImages():

  def LoadImage(orientation):
    filename = os.path.join("images", orientation.name.lower() + ".png")
    image = cv2.imread(filename)
    return image

  return dict([(o, LoadImage(o))
               for o in [board.SquareType.UP, board.SquareType.RIGHT,
                         board.SquareType.DOWN, board.SquareType.LEFT]])


def ShowSolution(images, puzzle, solution, frame, box):
  cell_size = np.array([box.w / 4, box.h / 4])
  for piece_type, piece, i, j in solution:
    top_left_loc = np.array([box.x, box.y]) + (np.array([j, i]) -
                                               np.array([1, 1])) * cell_size
    color = pieces.Colors[piece_type]
    piece_img = np.zeros_like(frame)
    for square in itertools.product(range(2), range(2)):
      if piece[square] == board.SquareType.AIR:
        continue

      loc = top_left_loc + np.array(square[::-1]) * cell_size
      piece_img = cv2.rectangle(piece_img, tuple(loc), tuple(loc + cell_size),
                                color, -2)

      if piece[square] in images:
        image = cv2.resize(images[piece[square]], tuple(cell_size))
        blend = np.zeros_like(piece_img)
        blend[loc[1]:loc[1] + cell_size[1], loc[0]:loc[0] + cell_size[
            0]] = image
        piece_img = cv2.addWeighted(piece_img, 1.0, blend, 1.0, 0)

    piece_gray = cv2.cvtColor(piece_img, cv2.COLOR_RGB2GRAY)
    _, piece_gray = cv2.threshold(piece_gray, 10, 255, cv2.THRESH_BINARY)
    _, contours, _ = cv2.findContours(piece_gray, cv2.RETR_EXTERNAL,
                                      cv2.CHAIN_APPROX_SIMPLE)
    piece_img = cv2.drawContours(piece_img, contours, -1, (255, 255, 255), 3)

    frame = cv2.addWeighted(frame, 1.0, piece_img, 0.7, 0)
    cv2.imshow("Planes", frame)


def main():
  try:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--image",
                        type=str,
                        help="Process input image. Using video camera insead")
    parser.add_argument("-v",
                        "--verbose",
                        action="store_true",
                        help="Enable debug prints")

    global Options
    Options = parser.parse_args()
    if Options.verbose:
      logging.getLogger('').handlers = []
      logging.basicConfig(level=logging.DEBUG)

    try:
      loader = solutions.AsyncLoader()
      loader.start()

      if Options.image:
        source = image_source.FileSource(Options.image)
      else:
        source = image_source.CameraSource()

      templates = LoadTemplates()
      images = LoadImages()

      while True:
        frame = source.NextFrame()
        cv2.imshow("Planes", frame)

        frame_bw = PrepareImage(frame)

        box = FindBoard(frame_bw)
        if not box:
          WaitKey(5)
          continue

        cells = ReadCells(frame_bw, box)
        objects = DetectObjects(templates, cells)
        constraints = DetectConstraints(templates, cells)

        puzzle = BuildPuzzleBoardFromObjects(objects)
        if Options.verbose:
          board.Print(puzzle)

        loader.join()
        matches = loader.db["board_to_solution"][hash(str(puzzle))]
        if not matches:
          WaitKey(5)
          logging.debug("Puzzle not found in solutions DB")
          continue

        logging.debug("Found {0} solutions in DB".format(len(matches)))
        matches = [m for m in matches if PassConstraints(constraints, m)]

        logging.debug("Found {0} solutions within constraints".format(len(
            matches)))
        for m in matches:
          ShowSolution(images, puzzle, m, frame, box)
          WaitKey(0)

    finally:
      logging.debug("Destroying windows")
      cv2.destroyAllWindows()

  except Exception, e:
    logging.error(traceback.format_exc())
    return e


if __name__ == "__main__":
  sys.exit(main())
