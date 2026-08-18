"""Puzzle: a generated, validated, and classified starting grid + its unique
solution, per the design doc's object model. Each Puzzle has a unique ID
(a content hash of its starting+solution grids, so regenerating the exact
same puzzle is naturally deduplicated) plus the raw difficulty signals an
Archive uses to produce a "sorted ID based on complexity."
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from grid import Grid


def _grid_key(grid: Grid) -> tuple:
    return tuple(int(v) for v in grid.cells.flatten())


def _compute_id(starting: Grid, solution: Grid) -> str:
    payload = repr(_grid_key(starting) + _grid_key(solution)).encode()
    return hashlib.sha256(payload).hexdigest()[:16]


@dataclass
class Puzzle:
    puzzle_id: str
    starting: Grid
    solution: Grid
    given_cells: int  # kept-cell count on the starting grid; fewer == harder
    solve_guesses: int  # Solver.SolveStats.guesses for the starting grid; more == harder
    line_solving_uses: int  # Solver.SolveStats.line_solving_uses; more == harder

    @classmethod
    def create(cls, starting: Grid, solution: Grid, given_cells: int, solve_guesses: int,
               line_solving_uses: int) -> "Puzzle":
        return cls(
            puzzle_id=_compute_id(starting, solution),
            starting=starting,
            solution=solution,
            given_cells=given_cells,
            solve_guesses=solve_guesses,
            line_solving_uses=line_solving_uses,
        )

    def to_dict(self) -> dict:
        return {
            "puzzle_id": self.puzzle_id,
            "starting": self.starting.cells.tolist(),
            "solution": self.solution.cells.tolist(),
            "given_cells": self.given_cells,
            "solve_guesses": self.solve_guesses,
            "line_solving_uses": self.line_solving_uses,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Puzzle":
        return cls(
            puzzle_id=data["puzzle_id"],
            starting=Grid.from_values(data["starting"]),
            solution=Grid.from_values(data["solution"]),
            given_cells=data["given_cells"],
            solve_guesses=data["solve_guesses"],
            line_solving_uses=data["line_solving_uses"],
        )
