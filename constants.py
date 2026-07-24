"""Shared constants for the Circles game (8x8 full-circle / empty-circle puzzle)."""

from enum import IntEnum


class Value(IntEnum):
    """A cell's value. BLANK only ever appears on starting/playing grids, never a solved grid."""

    BLANK = -1
    EMPTY = 0  # "O"
    FULL = 1  # filled circle


SYMBOLS = {Value.BLANK: " ", Value.EMPTY: "O", Value.FULL: "●"}

SIZE = 8
TARGET_COUNT = SIZE // 2  # each row/column needs this many FULL and this many EMPTY
CIRCLE_VALUES = (Value.FULL, Value.EMPTY)
