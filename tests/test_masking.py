import random

from constants import SIZE, Value
from generator import LocalExpansionGenerator
from masking import (
    avg_pairwise_distance,
    full_fraction_of,
    generate_puzzle,
    mask_grid,
    minimize_positions,
    sample_positions,
)
from solver import has_unique_solution, solve

BLANK = Value.BLANK


def _solved():
    grid, _ = LocalExpansionGenerator(rng=random.Random(3)).generate()
    return grid


def test_mask_grid_keeps_only_given_positions():
    solved = _solved()
    keep = [(0, 0), (3, 4), (7, 7)]
    masked = mask_grid(solved, keep)

    for r, c in keep:
        assert masked.get(r, c) == solved.get(r, c)
    kept_set = set(keep)
    for r in range(SIZE):
        for c in range(SIZE):
            if (r, c) not in kept_set:
                assert masked.get(r, c) == BLANK


def test_avg_pairwise_distance_of_two_points():
    assert avg_pairwise_distance([(0, 0), (0, 3)]) == 3.0
    assert avg_pairwise_distance([(0, 0)]) == 0.0


def test_full_fraction_of_matches_solved_values():
    solved = _solved()
    full_positions = [(r, c) for r in range(SIZE) for c in range(SIZE) if solved.get(r, c) == Value.FULL][:5]
    assert full_fraction_of(solved, full_positions) == 1.0


def test_sample_positions_returns_distinct_positions_with_requested_count():
    solved = _solved()
    rng = random.Random(1)
    positions = sample_positions(solved, rng, n=20, full_fraction=0.5, spread="uniform")
    assert len(positions) == 20
    assert len(set(positions)) == 20


def test_sample_positions_honors_full_fraction_target():
    solved = _solved()
    rng = random.Random(2)
    positions = sample_positions(solved, rng, n=16, full_fraction=0.75, spread="uniform")
    assert full_fraction_of(solved, positions) == 0.75


def test_spread_mode_yields_more_spread_than_clustered_on_average():
    solved = _solved()
    spread_distances = []
    clustered_distances = []
    for seed in range(15):
        spread_positions = sample_positions(solved, random.Random(seed), n=10, spread="spread")
        clustered_positions = sample_positions(solved, random.Random(seed), n=10, spread="clustered")
        spread_distances.append(avg_pairwise_distance(spread_positions))
        clustered_distances.append(avg_pairwise_distance(clustered_positions))

    avg_spread = sum(spread_distances) / len(spread_distances)
    avg_clustered = sum(clustered_distances) / len(clustered_distances)
    assert avg_spread > avg_clustered


def test_generate_puzzle_returns_a_unique_solution_starting_grid():
    solved = _solved()
    starting, positions, stats = generate_puzzle(solved, rng=random.Random(5))

    assert starting is not None
    assert has_unique_solution(starting)
    assert len(positions) == stats.final_cells
    solutions, _ = solve(starting, limit=1)
    assert (solutions[0].cells == solved.cells).all()


def test_generate_puzzle_minimization_does_not_increase_cell_count():
    solved = _solved()
    starting, positions, stats = generate_puzzle(solved, rng=random.Random(6), target_n=30)
    assert stats.final_cells <= stats.starting_cells
    assert len(positions) == stats.final_cells


def test_minimize_positions_keeps_a_unique_solution_and_cannot_drop_further():
    solved = _solved()
    rng = random.Random(8)
    positions = sample_positions(solved, rng, n=30, full_fraction=0.75, spread="spread")
    assert has_unique_solution(mask_grid(solved, positions))

    minimized = minimize_positions(solved, positions, rng)
    assert has_unique_solution(mask_grid(solved, minimized))
    assert len(minimized) <= len(positions)

    # No single cell can be removed from the minimized set without losing uniqueness.
    for pos in minimized:
        candidate = [p for p in minimized if p != pos]
        assert not has_unique_solution(mask_grid(solved, candidate))


def test_generate_puzzle_returns_none_when_target_n_is_hopelessly_small():
    solved = _solved()
    starting, positions, stats = generate_puzzle(solved, rng=random.Random(9), target_n=2, max_attempts=5)
    assert starting is None
    assert positions is None
    assert stats.sample_attempts == 5
