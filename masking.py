"""Masking: turning a solved Grid into a starting puzzle by blanking all but
a chosen subset of cells, per the design doc's "backward approach" ("mask
cells until only a few cells are remaining").

`generate_puzzle` is the entry point: sample-and-reject to find *any*
unique-solution mask, then greedily remove further cells while uniqueness
holds, to get near the fewest starting cells that particular draw can reach
(the design doc's stated difficulty signal -- "how many more cells could
have been masked while still yielding a starting point with a unique
solution"). The sampling defaults (spread="spread", full_fraction=0.75,
starting from n=30) come directly from the Monte Carlo sweep run against
the Solver: farthest-point-spread cells with a slight skew toward FULL hit
~90%+ uniqueness at n=30, versus ~0% below n~14 regardless of arrangement --
so it's cheap to resample at the high end and let minimization do the work
of finding how far a given solved grid can actually be pushed.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from constants import SIZE, Value
from grid import Grid
from solver import has_unique_solution


def mask_grid(solved: Grid, keep_positions) -> Grid:
    """Returns a new Grid with every cell blanked except those in
    `keep_positions`, which keep their value from `solved`."""
    masked = Grid()
    for r, c in keep_positions:
        masked.set(r, c, solved.get(r, c))
    return masked


def sample_positions(solved: Grid, rng: random.Random, n: int,
                      full_fraction: float = 0.5, spread: str = "uniform") -> list:
    """Samples `n` distinct (row, col) positions from `solved`, with:
    - `full_fraction`: target share of the sample drawn from FULL cells
      (the rest from EMPTY cells) -- lets a sweep control puzzle "polarity"
      independent of what a uniform-random draw happens to land on.
    - `spread`: "uniform" (plain random sample), "clustered" (biased toward
      one random anchor cell), or "spread" (greedy farthest-point sampling,
      biased toward maximal coverage).
    """
    full_cells = [(r, c) for r in range(SIZE) for c in range(SIZE) if solved.get(r, c) == Value.FULL]
    empty_cells = [(r, c) for r in range(SIZE) for c in range(SIZE) if solved.get(r, c) == Value.EMPTY]

    n_full = min(round(n * full_fraction), len(full_cells))
    n_empty = min(n - n_full, len(empty_cells))
    n_full = min(n - n_empty, len(full_cells))

    if spread == "uniform":
        chosen = rng.sample(full_cells, n_full) + rng.sample(empty_cells, n_empty)
    elif spread == "clustered":
        anchor = (rng.randrange(SIZE), rng.randrange(SIZE))
        chosen = _closest_sample(full_cells, n_full, anchor) + _closest_sample(empty_cells, n_empty, anchor)
    elif spread == "spread":
        chosen = _farthest_point_sample(rng, full_cells, n_full) + _farthest_point_sample(rng, empty_cells, n_empty)
    else:
        raise ValueError(f"unknown spread mode: {spread!r}")

    rng.shuffle(chosen)
    return chosen


def avg_pairwise_distance(positions) -> float:
    total, count = 0.0, 0
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            total += _distance(positions[i], positions[j])
            count += 1
    return total / count if count else 0.0


def full_fraction_of(solved: Grid, positions) -> float:
    if not positions:
        return 0.0
    full = sum(1 for r, c in positions if solved.get(r, c) == Value.FULL)
    return full / len(positions)


def _distance(a, b) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _closest_sample(candidates, k, anchor) -> list:
    return sorted(candidates, key=lambda p: _distance(p, anchor))[:k]


def _farthest_point_sample(rng: random.Random, candidates, k) -> list:
    if k <= 0:
        return []
    pool = list(candidates)
    chosen = [pool.pop(rng.randrange(len(pool)))]
    while len(chosen) < k and pool:
        best_index, best_distance = 0, -1.0
        for i, candidate in enumerate(pool):
            distance = min(_distance(candidate, picked) for picked in chosen)
            if distance > best_distance:
                best_index, best_distance = i, distance
        chosen.append(pool.pop(best_index))
    return chosen


@dataclass
class MaskingStats:
    sample_attempts: int = 0  # resample-until-unique attempts before minimization
    starting_cells: int = 0  # kept-cell count of the first unique mask found
    final_cells: int = 0  # kept-cell count after minimization


def find_unique_starting_positions(solved: Grid, rng: random.Random, n: int,
                                    full_fraction: float = 0.75, spread: str = "spread",
                                    max_attempts: int = 200):
    """Repeatedly samples `n` positions until the resulting mask has a unique
    solution, or gives up after `max_attempts` (returns None -- the caller
    should retry with a larger `n`, per the sweep's floor around n~14)."""
    for attempt in range(1, max_attempts + 1):
        positions = sample_positions(solved, rng, n=n, full_fraction=full_fraction, spread=spread)
        if has_unique_solution(mask_grid(solved, positions)):
            return positions, attempt
    return None, max_attempts


def minimize_positions(solved: Grid, positions, rng: random.Random) -> list:
    """Greedily drops cells from `positions`, one at a time in random order,
    keeping each drop only if the mask still has a unique solution. A single
    pass, so the result is locally minimal for this removal order, not
    necessarily globally minimal (finding the true minimum is NP-hard in
    general) -- this is the standard technique Sudoku-style generators use."""
    order = list(positions)
    rng.shuffle(order)
    kept = list(positions)
    for pos in order:
        candidate = [p for p in kept if p != pos]
        if has_unique_solution(mask_grid(solved, candidate)):
            kept = candidate
    return kept


def generate_puzzle(solved: Grid, rng: random.Random | None = None, target_n: int = 30,
                     full_fraction: float = 0.75, spread: str = "spread",
                     max_attempts: int = 200, minimize: bool = True):
    """Masks `solved` down to a starting puzzle with a unique solution.
    Returns (starting_grid, kept_positions, MaskingStats), or (None, None,
    stats) if no unique mask was found at `target_n` within `max_attempts`."""
    rng = rng or random.Random()
    stats = MaskingStats()
    positions, attempts = find_unique_starting_positions(
        solved, rng, target_n, full_fraction=full_fraction, spread=spread, max_attempts=max_attempts)
    stats.sample_attempts = attempts
    if positions is None:
        return None, None, stats
    stats.starting_cells = len(positions)

    if minimize:
        positions = minimize_positions(solved, positions, rng)
    stats.final_cells = len(positions)
    return mask_grid(solved, positions), positions, stats
