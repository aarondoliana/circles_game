"""Masking: turning a solved Grid into a starting puzzle by blanking all but
a chosen subset of cells, per the design doc's "backward approach" ("mask
cells until only a few cells are remaining").

This module currently holds the sampling/measurement primitives needed to
study *which* subsets of kept cells tend to yield a unique solution --
number of kept cells, how spread out they are, and what fraction are FULL --
before committing to a specific masking heuristic. `solver.has_unique_solution`
(or `solver.solve` with a small limit) is what actually checks a candidate
starting grid.
"""

from __future__ import annotations

import random

from constants import SIZE, Value
from grid import Grid


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
