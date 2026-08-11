"""Solver: R2/R3/brute-force-line-solving constraint propagation with
guess-and-backtrack, per the "Algorithm" section of specs/design_doc.md.

Propagation follows the doc's hierarchy: R2 > R3 > brute-force-line-solving >
recursive backtracking. R2 and R3 are drained to a combined fixpoint first,
since they're the cheapest checks (O(line length) each) and brute-force
line-solving is a strict superset of what they can force (see below) --
running it before R2/R3 have exhausted themselves would mean it silently
claims cells that R2/R3 alone could have solved, which would corrupt
`stats.line_solving_uses` as a difficulty signal (see the "Solve stats"
section of the design doc's Hint provider notes: the point is to know
whether a puzzle needed *more* than R2/R3 reasoning). Only once R2/R3 stall
does brute-force-line-solving get one pass; if that makes progress, we loop
back to R2/R3 (a line-solving fill can unlock new R2/R3 moves elsewhere),
continuing until a full outer pass across all three makes no progress.
Grid-wide backtracking is reserved for genuine inter-line dependencies that
no amount of single-line reasoning (R2, R3, or brute-force-line-solving) can
resolve. When a full pass fills nothing and the grid is still incomplete,
that's the doc's "exception for qualitative review" -- a guess is required.
Each such point is counted in `SolveStats.guesses`; together with
`SolveStats.line_solving_uses`, these double as cheap signals for future
puzzle-difficulty classification (0 of either == solvable by pure R2/R3).

R2, R3, and the "is this triplet/line R2/R3-consistent" primitives they're
built on are defined once in `validator.py` (`count_full_empty`,
`is_alternating_triplet`, `line_violates_r2`, `line_violates_r3`) and
imported here, rather than re-derived, so the rule definitions can't drift
out of sync between the validator and the solver:

R2: whenever a row/column already has TARGET_COUNT of one value, its
remaining blanks are forced to the other value.
R3: for any three consecutive cells with exactly one blank, if only one of
the two candidate values keeps the triplet from becoming an alternating
⚫O⚫/O⚫O, that value is forced.
Brute-force-line-solving: per the design doc's "Note on additional solver
patterns", this generalizes the doc's named single-line deduction patterns
(group-of-three, quintuplet/gap, adjacency inference, ...) into one
mechanism instead of hand-coding each: for a given line, enumerate every way
to assign FULL/EMPTY to its blank cells that (a) hits the line's remaining
R2 counts and (b) keeps the whole line R3-valid, then force any blank cell
that holds the same value across every such valid completion. This is
strictly more powerful than the per-triplet R3 check above (which only ever
looks at one triplet at a time) and provably subsumes every one of the named
patterns, since any of them amounts to "some assignment would make an
otherwise-valid full-line completion impossible." At SIZE=8 there are at
most C(8, 4) = 70 candidate completions for the emptiest line, so this stays
cheap. The named patterns themselves are parked (see the "Solver pattern
naming, deferred to the Hint provider" TODO) rather than implemented
individually -- they're for the future Hint provider, which needs them
named and ranked by complexity, not for the solver, which just needs the
forced cells.

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
from itertools import combinations

from constants import CIRCLE_VALUES, SIZE, TARGET_COUNT, Value
from grid import Grid
from validator import count_full_empty, is_alternating_triplet, line_violates_r3, validate


@dataclass
class SolveStats:
    guesses: int = 0
    line_solving_uses: int = 0  # number of propagate() passes where brute-force-line-solving contributed a move


def find_r2_forced_moves(grid: Grid) -> list:
    moves = []
    for r in range(SIZE):
        moves.extend(_r2_line_moves(grid.row(r), lambda i, v, r=r: (r, i, v)))
    for c in range(SIZE):
        moves.extend(_r2_line_moves(grid.col(c), lambda i, v, c=c: (i, c, v)))
    return moves


def _r2_line_moves(line, make_move) -> list:
    full, empty = count_full_empty(line)
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
            if is_alternating_triplet(a, b, c):
                continue
            legal.append(candidate)
        if len(legal) == 1:
            moves.append(make_move(i + pos, legal[0]))
    return moves


def find_line_forced_moves(grid: Grid) -> list:
    moves = []
    for r in range(SIZE):
        moves.extend(_line_forced_moves(grid.row(r), lambda i, v, r=r: (r, i, v)))
    for c in range(SIZE):
        moves.extend(_line_forced_moves(grid.col(c), lambda i, v, c=c: (i, c, v)))
    return moves


def _line_forced_moves(line, make_move) -> list:
    blanks = [i for i, v in enumerate(line) if v == Value.BLANK]
    if not blanks:
        return []

    full, empty = count_full_empty(line)
    remaining_full = TARGET_COUNT - full
    remaining_empty = TARGET_COUNT - empty
    if remaining_full < 0 or remaining_empty < 0 or remaining_full + remaining_empty != len(blanks):
        return []  # already contradictory; propagate()'s validate() catches this

    completions = []
    for full_positions in combinations(blanks, remaining_full):
        trial = list(line)
        for i in blanks:
            trial[i] = Value.FULL if i in full_positions else Value.EMPTY
        if not line_violates_r3(trial):
            completions.append(trial)

    moves = []
    for i in blanks:
        values_at_i = {completion[i] for completion in completions}
        if len(values_at_i) == 1:
            moves.append(make_move(i, Value(values_at_i.pop())))
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


def propagate(grid: Grid, stats: SolveStats | None = None) -> bool:
    """Drains R2 and R3 to a combined fixpoint, then runs brute-force
    line-solving once; if that makes progress, loops back to R2/R3,
    continuing until a full outer pass across all three makes no progress.
    Gating line-solving behind R2/R3 exhausting themselves (rather than
    interleaving all three every pass) is what makes `stats.line_solving_uses`
    a trustworthy signal: it only increments when R2/R3 truly couldn't
    proceed without it. Returns False if a contradiction is detected (grid
    can no longer reach a valid solution), True otherwise (grid may be
    incomplete)."""
    while True:
        core_progress = False
        while True:
            r2_progress = _drain(find_r2_forced_moves, grid)
            if not validate(grid).is_valid:
                return False
            r3_progress = _drain(find_r3_forced_moves, grid)
            if not validate(grid).is_valid:
                return False
            if not (r2_progress or r3_progress):
                break
            core_progress = True

        line_progress = _drain(find_line_forced_moves, grid)
        if not validate(grid).is_valid:
            return False
        if line_progress and stats is not None:
            stats.line_solving_uses += 1

        if not (core_progress or line_progress):
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
    if not propagate(grid, stats):
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
