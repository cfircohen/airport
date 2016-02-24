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
import numpy as np
from enum import Enum


class SquareType(Enum):
  AIR = 0
  UP = 1
  RIGHT = 2
  DOWN = 3
  LEFT = 4
  GLASS = 5
  ANY = 6

  def __add__(self, other):
    if self is SquareType.AIR:
      return SquareType(other)
    if other is SquareType.AIR:
      return SquareType(self)
    raise ValueError("Can not add {0} with {1}".format(self, other))


# A 6x6 board where the middle 4x4 squars hold the puzzle
# pieces.
def Empty():
  return np.array([SquareType.AIR] * 36, dtype='O').reshape(6, 6)


def IsSolved(board):
  return (all(board[0, :] == np.array([SquareType.AIR] * 6)) and
          all(board[:, 0] == np.array([SquareType.AIR] * 6)) and
          all(board[5, :] == np.array([SquareType.AIR] * 6)) and
          all(board[:, 5] == np.array([SquareType.AIR] * 6)))


def Print(board):
  for i in range(6):
    for j in range(6):
      print "{0:^10}".format(board[i][j].name),
    print
