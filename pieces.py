import numpy as np
from board import SquareType
import color
from enum import Enum

PieceType = Enum("PieceType", "L_RED L_GREEN L_BLUE L_BLACK I_RED I_ORANGE")


def BuildOrientations(piece):

  def RotateValue(v):
    # Rotate block with orientation
    if v in (SquareType.UP, SquareType.RIGHT, SquareType.DOWN, SquareType.LEFT):
      if v is SquareType.LEFT:
        return SquareType.UP
      return SquareType(v.value + 1)
    # AIR/GLASS don't change value
    return v

  orientations = []
  for i in range(4):
    # Rotate the piece 90deg clock wise
    new = np.zeros_like(piece)
    new[0, 0] = RotateValue(piece[1, 0])
    new[0, 1] = RotateValue(piece[0, 0])
    new[1, 0] = RotateValue(piece[1, 1])
    new[1, 1] = RotateValue(piece[0, 1])
    orientations.append(new)
    piece = new

  return orientations

# Piece is a 2x2 block. For example the red L shaped piece looks like:
#    GLASS  AIR
#    RIGHT  GLASS
#
# We store all 4 possible orientations for each piece in the following
# dictionary.
Orientations = {
    PieceType.L_RED: BuildOrientations(np.array(
        [SquareType.GLASS, SquareType.AIR, SquareType.RIGHT, SquareType.GLASS
        ]).reshape((2, 2))),
    PieceType.L_BLACK: BuildOrientations(np.array(
        [SquareType.GLASS, SquareType.AIR, SquareType.LEFT, SquareType.GLASS
        ]).reshape((2, 2))),
    PieceType.L_BLUE: BuildOrientations(np.array(
        [SquareType.DOWN, SquareType.AIR, SquareType.GLASS, SquareType.GLASS
        ]).reshape((2, 2))),
    PieceType.I_ORANGE: BuildOrientations(np.array(
        [SquareType.DOWN, SquareType.AIR, SquareType.GLASS, SquareType.AIR
        ]).reshape((2, 2))),
    PieceType.I_RED: BuildOrientations(np.array(
        [SquareType.LEFT, SquareType.AIR, SquareType.GLASS, SquareType.AIR
        ]).reshape((2, 2))),
    PieceType.L_GREEN: BuildOrientations(np.array(
        [SquareType.GLASS, SquareType.AIR, SquareType.GLASS, SquareType.UP
        ]).reshape((2, 2))),
}

Colors = {PieceType.L_RED: color.Color("darkred"),
          PieceType.L_GREEN: color.Color("green"),
          PieceType.L_BLUE: color.Color("blue"),
          PieceType.L_BLACK: color.Color("black"),
          PieceType.I_RED: color.Color("red"),
          PieceType.I_ORANGE: color.Color("yellow")}
