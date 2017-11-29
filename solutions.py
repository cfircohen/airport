#!/usr/local/bin/python
#
"""Copyright 2016 Google Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import collections
import copy
import cPickle as pickle
import itertools
import logging
import os
#import random
import sys
#import time
import traceback
import threading

import argparse
import numpy as np

import board
import pieces

DB_FILENAME = "solutions.pickle"


def store(key, value):
  logging.debug("Saving {}".format(key))
  save = {}
  global DB_FILENAME
  if os.path.exists(DB_FILENAME):
    with open(DB_FILENAME, "rb") as f:
      save = pickle.load(f)

  with open(DB_FILENAME, "wb") as f:
    save[key] = value
    pickle.dump(save, f, pickle.HIGHEST_PROTOCOL)


def load(key):
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


def find_all_solutions():
  all_solutions = []

  def search(current, left, solution):
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
        search(new, copy.copy(left),
               copy.copy(solution) + [(piece_type, piece, i, j)])
      except ValueError:
        pass

  search(board.Empty(), list(pieces.PieceType), [])

  logging.info("found {} solutions".format(len(all_solutions)))
  return all_solutions


def place_pieces(locations):
  b = board.Empty()
  for piece_type, piece, i, j in locations:
    b[i:i + 2, j:j + 2] += piece
  # Remove glass
  b[np.where(b == board.SquareType.GLASS)] = board.SquareType.AIR
  return b


def hash_by_exact_orientation(b):
  # No need to change the squares in board
  return hash(str(b))


def hash_by_any_orientation(b):
  b[np.where(b == board.SquareType.UP)] = board.SquareType.ANY
  b[np.where(b == board.SquareType.RIGHT)] = board.SquareType.ANY
  b[np.where(b == board.SquareType.DOWN)] = board.SquareType.ANY
  b[np.where(b == board.SquareType.LEFT)] = board.SquareType.ANY
  return hash(str(b))


def build_hashable_solutions():
  raw_solutions = load("raw_solutions")
  solutions = collections.defaultdict(list)
  for locations in raw_solutions:
    b = place_pieces(locations)
    solutions[hash_by_exact_orientation(b)].append(locations)
    solutions[hash_by_any_orientation(b)].append(locations)

  store("board_to_solution", solutions)


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

    #all_solutions = find_all_solutions()
    #store("raw_solutions", all_solutions)

    build_hashable_solutions()

  except Exception as e:
    logging.error(traceback.format_exc())
    return e


if __name__ == "__main__":
  sys.exit(main())
