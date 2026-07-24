"""Generator: "Full puzzle generation #2" (local expansion + memory stack) from
specs/design_doc.md.

Fills the grid cell by cell (row-major). Each row and column keeps a "memory
stack" of how many FULL/EMPTY circles it still owes (starts at TARGET_COUNT
each). At every cell, candidate values are those still available in both the
row's and column's remaining counts, and that don't create an R3-violating
triplet with the two preceding cells in the row/column. The design doc's
lookahead repair heuristic is applied to steer away from likely dead ends: if
placing a value would use up the LAST remaining instance of that value in a
row/column, and the immediately preceding cell in that row/column was the
*other* value, prefer the alternative candidate instead (this is what avoids
sequences like "O,O,O,*,*,O" which force an unsolvable "*,O,*" a couple of
cells later).

If a cell has no legal candidate at all, generation crashes and restarts from
an empty grid, per the design doc ("the puzzle construction crashes and
starts over").
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from constants import CIRCLE_VALUES, SIZE, TARGET_COUNT, Value
from grid import Grid


@dataclass
class GenerationStats:
    attempts: int = 0


class GenerationFailed(RuntimeError):
    pass


class LocalExpansionGenerator:
    def __init__(self, rng: random.Random | None = None, max_attempts: int = 10_000,
                 use_repair_heuristic: bool = True):
        self.rng = rng or random.Random()
        self.max_attempts = max_attempts
        self.use_repair_heuristic = use_repair_heuristic

    def generate(self) -> tuple[Grid, GenerationStats]:
        stats = GenerationStats()
        for attempt in range(1, self.max_attempts + 1):
            stats.attempts = attempt
            grid = self._attempt()
            if grid is not None:
                return grid, stats
        raise GenerationFailed(f"no valid grid found in {self.max_attempts} attempts")

    def _attempt(self) -> Grid | None:
        grid = Grid()
        row_remaining = [{v: TARGET_COUNT for v in CIRCLE_VALUES} for _ in range(SIZE)]
        col_remaining = [{v: TARGET_COUNT for v in CIRCLE_VALUES} for _ in range(SIZE)]

        for r in range(SIZE):
            for c in range(SIZE):
                value = self._select_value(grid, row_remaining[r], col_remaining[c], r, c)
                if value is None:
                    return None
                grid.set(r, c, value)
                row_remaining[r][value] -= 1
                col_remaining[c][value] -= 1
        return grid

    def _select_value(self, grid: Grid, row_remaining: dict, col_remaining: dict,
                       r: int, c: int) -> Value | None:
        candidates = [
            v for v in CIRCLE_VALUES
            if row_remaining[v] > 0 and col_remaining[v] > 0
            and not self._violates_r3(grid, r, c, v)
        ]
        if not candidates:
            return None
        if len(candidates) == 1 or not self.use_repair_heuristic:
            return self.rng.choice(candidates)

        safe = [v for v in candidates if not self._is_risky(row_remaining, col_remaining, grid, r, c, v)]
        return self.rng.choice(safe or candidates)

    @staticmethod
    def _violates_r3(grid: Grid, r: int, c: int, value: Value) -> bool:
        if c >= 2:
            a, b = grid.get(r, c - 2), grid.get(r, c - 1)
            if a == value and b != value:
                return True
        if r >= 2:
            a, b = grid.get(r - 2, c), grid.get(r - 1, c)
            if a == value and b != value:
                return True
        return False

    @staticmethod
    def _is_risky(row_remaining: dict, col_remaining: dict, grid: Grid,
                   r: int, c: int, value: Value) -> bool:
        """True if placing `value` here would strand the row/column's last
        instance of `value` right after its opposite, which the design doc
        identifies as the pattern that forces an R3 violation a few cells
        later."""
        row_risky = row_remaining[value] == 1 and c > 0 and grid.get(r, c - 1) != value
        col_risky = col_remaining[value] == 1 and r > 0 and grid.get(r - 1, c) != value
        return row_risky or col_risky
