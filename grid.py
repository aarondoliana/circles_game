"""The 8x8 Grid: a thin wrapper around an int matrix of Value entries."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from constants import SIZE, SYMBOLS, Value


@dataclass
class Grid:
    cells: np.ndarray = field(
        default_factory=lambda: np.full((SIZE, SIZE), Value.BLANK, dtype=np.int8)
    )

    @classmethod
    def from_values(cls, values) -> "Grid":
        cells = np.array(values, dtype=np.int8)
        if cells.shape != (SIZE, SIZE):
            raise ValueError(f"expected a {SIZE}x{SIZE} grid, got shape {cells.shape}")
        return cls(cells)

    def get(self, row: int, col: int) -> Value:
        return Value(self.cells[row, col])

    def set(self, row: int, col: int, value: Value) -> None:
        self.cells[row, col] = value

    def row(self, index: int) -> np.ndarray:
        return self.cells[index, :]

    def col(self, index: int) -> np.ndarray:
        return self.cells[:, index]

    def is_complete(self) -> bool:
        return bool(np.all(self.cells != Value.BLANK))

    def copy(self) -> "Grid":
        return Grid(self.cells.copy())

    def __str__(self) -> str:
        return "\n".join(
            " ".join(SYMBOLS[Value(v)] for v in self.row(r)) for r in range(SIZE)
        )
