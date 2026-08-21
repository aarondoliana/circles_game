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

    def inverted(self) -> "Grid":
        """Returns a new Grid with FULL/EMPTY swapped everywhere (⚫↔O) and
        BLANK cells left as BLANK. R2 (count balance) and R3 (squeeze
        pattern) both depend only on equality relationships between cells,
        not on which value is which, so an inverted grid is valid and
        uniquely solvable, at the same difficulty, iff the original is."""
        # FULL(1)-EMPTY(0) swap via 1-v; BLANK(-1) would map to 2, so it's
        # special-cased back to BLANK below rather than left to fall out.
        swapped = Value.FULL + Value.EMPTY - self.cells
        cells = np.where(self.cells == Value.BLANK, Value.BLANK, swapped).astype(np.int8)
        return Grid(cells)

    def __str__(self) -> str:
        return "\n".join(
            " ".join(SYMBOLS[Value(v)] for v in self.row(r)) for r in range(SIZE)
        )
