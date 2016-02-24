#!/usr/local/bin/python
import sys
import os
import time
import random
import numpy as np
import logging
import argparse
import traceback
import collections
import threading
import cPickle as pickle
import copy
import itertools
import board
import pieces

DB_FILENAME = "solutions.pickle"


def Store(key, value):
  logging.debug("Saving {}".format(key))
  save = {}
  global DB_FILENAME
  if os.path.exists(DB_FILENAME):
    with open(DB_FILENAME, "rb") as f:
      save = pickle.load(f)

  with open(DB_FILENAME, "wb") as f:
    save[key] = value
    pickle.dump(save, f, pickle.HIGHEST_PROTOCOL)


def Load(key):
  global DB_FILENAME
  with open(DB_FILENAME, "rb") as f:
    save = pickle.load(f)
    return save[key]


class AsyncLoader(threading.Thread):

  def run(self):
    global DB_FILENAME
    with open(DB_FILENAME, "rb") as f:
      self.db = pickle.load(f)
    logging.info("Done loading solutions")


def FindAllSolutions():
  all_solutions = []

  def Search(current, left, solution):
    if not board.IsSolved(current):
      return

    if not left:
      all_solutions.append(solution)
      return

    piece_type = left.pop()
    for piece, i, j in itertools.product(pieces.Orientations[piece_type],
                                         range(5), range(5)):
      try:
        new = copy.copy(current)
        new[i:i + 2, j:j + 2] += piece
        Search(new, copy.copy(left),
               copy.copy(solution) + [(piece_type, piece, i, j)])
      except ValueError:
        pass

  Search(board.Empty(), list(pieces.PieceType), [])

  logging.info("found {} solutions".format(len(all_solutions)))
  return all_solutions


def PlacePieces(locations):
  b = board.Empty()
  for piece_type, piece, i, j in locations:
    b[i:i + 2, j:j + 2] += piece
  # Remove glass
  b[np.where(b == board.SquareType.GLASS)] = board.SquareType.AIR
  return b


def HashByExactOrientation(b):
  # No need to change the squares in board
  return hash(str(b))


def HashByAnyOrientation(b):
  b[np.where(b == board.SquareType.UP)] = board.SquareType.ANY
  b[np.where(b == board.SquareType.RIGHT)] = board.SquareType.ANY
  b[np.where(b == board.SquareType.DOWN)] = board.SquareType.ANY
  b[np.where(b == board.SquareType.LEFT)] = board.SquareType.ANY
  return hash(str(b))


def BuildHashableSolutions():
  raw_solutions = Load("raw_solutions")
  solutions = collections.defaultdict(list)
  for locations in raw_solutions:
    b = PlacePieces(locations)
    solutions[HashByExactOrientation(b)].append(locations)
    solutions[HashByAnyOrientation(b)].append(locations)

  Store("board_to_solution", solutions)


def main():
  try:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-v",
                        "--verbose",
                        action="store_true",
                        help="Enable debug prints")

    args = parser.parse_args()
    if args.verbose:
      logging.getLogger('').handlers = []
      logging.basicConfig(level=logging.DEBUG)

    #all_solutions = FindAllSolutions()
    #Store("raw_solutions", all_solutions)

    BuildHashableSolutions()

  except Exception, e:
    logging.error(traceback.format_exc())
    return e


if __name__ == "__main__":
  sys.exit(main())
