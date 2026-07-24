"""Solver: R3-then-R2 constraint propagation with guess-and-backtrack, per the
"Algorithm" section of specs/design_doc.md.

Propagation order follows the doc exactly: drain all R3-solvable
configurations to a fixpoint, then drain all R2-solvable configurations to a
fixpoint, then loop back to R3 (since an R2 fill can unlock new R3 moves).
When a full R3-then-R2 pass fills nothing and the grid is still incomplete,
that's the doc's "exception for qualitative review" -- a guess is required
because the puzzle can no longer be advanced by R2/R3 reasoning alone. Each
such point is counted in `SolveStats.guesses`, which doubles as a cheap
signal for future puzzle-difficulty classification (0 guesses == solvable by
pure logic).

R2: whenever a row/column already has TARGET_COUNT of one value, its
remaining blanks are forced to the other value.
R3: for any three consecutive cells with exactly one blank, if only one of
the two candidate values keeps the triplet from becoming an alternating
⚫O⚫/O⚫O, that value is forced.

One deliberate deviation from the doc's backtracking description: when both
values of a guessed cell dead-end, the doc has you try a *different* cell at
the same saved state before giving up on it. That extra step doesn't change
which solutions get found -- exhausting both domain values of any single
unassigned cell is already a sound and complete test of whether a state can
reach a solution, regardless of which cell you branch on. So this
implementation just does plain recursive backtracking on one cell per node
(trying both values, backtracking on failure), which is simpler and does the
same work without the redundant cell-switching.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from constants import CIRCLE_VALUES, SIZE, TARGET_COUNT, Value
from grid import Grid
from validator import validate


@dataclass
class SolveStats:
    guesses: int = 0


def find_r2_forced_moves(grid: Grid) -> list:
    moves = []
    for r in range(SIZE):
        moves.extend(_r2_line_moves(grid.row(r), lambda i, v, r=r: (r, i, v)))
    for c in range(SIZE):
        moves.extend(_r2_line_moves(grid.col(c), lambda i, v, c=c: (i, c, v)))
    return moves


def _r2_line_moves(line, make_move) -> list:
    full = int((line == Value.FULL).sum())
    empty = int((line == Value.EMPTY).sum())
    if full == TARGET_COUNT and empty < TARGET_COUNT:
        forced = Value.EMPTY
    elif empty == TARGET_COUNT and full < TARGET_COUNT:
        forced = Value.FULL
    else:
        return []
    return [make_move(i, forced) for i, v in enumerate(line) if v == Value.BLANK]


def find_r3_forced_moves(grid: Grid) -> list:
    moves = []
    for r in range(SIZE):
        moves.extend(_r3_line_moves(grid.row(r), lambda i, v, r=r: (r, i, v)))
    for c in range(SIZE):
        moves.extend(_r3_line_moves(grid.col(c), lambda i, v, c=c: (i, c, v)))
    return moves


def _r3_line_moves(line, make_move) -> list:
    moves = []
    for i in range(SIZE - 2):
        triplet = [Value(v) for v in line[i:i + 3]]
        blanks = [j for j, v in enumerate(triplet) if v == Value.BLANK]
        if len(blanks) != 1:
            continue
        pos = blanks[0]
        legal = []
        for candidate in CIRCLE_VALUES:
            trial = list(triplet)
            trial[pos] = candidate
            a, b, c = trial
            if a == c and b != a:
                continue  # would form the forbidden alternating triplet
            legal.append(candidate)
        if len(legal) == 1:
            moves.append(make_move(i + pos, legal[0]))
    return moves


def _drain(find_moves, grid: Grid) -> bool:
    """Applies `find_moves(grid)` repeatedly until it finds nothing new.
    Returns whether any cell was filled."""
    progressed = False
    while True:
        moves = [(r, c, v) for r, c, v in find_moves(grid) if grid.get(r, c) == Value.BLANK]
        if not moves:
            return progressed
        for r, c, v in moves:
            if grid.get(r, c) == Value.BLANK:
                grid.set(r, c, v)
        progressed = True


def propagate(grid: Grid) -> bool:
    """Drains R3 then R2 to a fixpoint, looping back to R3 as long as either
    made progress. Returns False if a contradiction is detected (grid can no
    longer reach a valid solution), True otherwise (grid may be incomplete)."""
    while True:
        r3_progress = _drain(find_r3_forced_moves, grid)
        if not validate(grid).is_valid:
            return False
        r2_progress = _drain(find_r2_forced_moves, grid)
        if not validate(grid).is_valid:
            return False
        if not (r3_progress or r2_progress):
            return True


def _pick_blank_cell(grid: Grid):
    for r in range(SIZE):
        for c in range(SIZE):
            if grid.get(r, c) == Value.BLANK:
                return r, c
    return None


def solve(grid: Grid, limit: int = 1, rng: random.Random | None = None):
    """Returns (solutions, stats). `solutions` holds up to `limit` distinct
    complete, valid grids reachable from `grid` (which may be partially
    filled); an empty list means no solution exists. Pass limit=2 to cheaply
    test uniqueness."""
    rng = rng or random.Random()
    solutions: list = []
    stats = SolveStats()
    _search(grid.copy(), solutions, limit, rng, stats)
    return solutions, stats


def _search(grid: Grid, solutions: list, limit: int, rng: random.Random, stats: SolveStats) -> None:
    if len(solutions) >= limit:
        return
    if not propagate(grid):
        return

    cell = _pick_blank_cell(grid)
    if cell is None:
        if validate(grid).is_valid:
            solutions.append(grid.copy())
        return

    stats.guesses += 1
    r, c = cell
    values = list(CIRCLE_VALUES)
    rng.shuffle(values)
    for value in values:
        if len(solutions) >= limit:
            return
        trial = grid.copy()
        trial.set(r, c, value)
        _search(trial, solutions, limit, rng, stats)


def has_unique_solution(grid: Grid) -> bool:
    solutions, _ = solve(grid, limit=2)
    return len(solutions) == 1
