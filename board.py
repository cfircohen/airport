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
