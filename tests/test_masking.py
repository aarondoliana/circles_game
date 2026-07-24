import random

from constants import SIZE, Value
from generator import LocalExpansionGenerator
from masking import avg_pairwise_distance, full_fraction_of, mask_grid, sample_positions

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
