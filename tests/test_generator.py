import random

from constants import SIZE, TARGET_COUNT, Value
from generator import LocalExpansionGenerator
from validator import validate


def test_generated_grid_is_complete_and_valid():
    gen = LocalExpansionGenerator(rng=random.Random(0))
    grid, stats = gen.generate()

    assert grid.is_complete()
    result = validate(grid)
    assert result.is_valid, result
    assert stats.attempts >= 1


def test_generated_grid_has_balanced_rows_and_columns():
    gen = LocalExpansionGenerator(rng=random.Random(1))
    grid, _ = gen.generate()

    for i in range(SIZE):
        assert int((grid.row(i) == Value.FULL).sum()) == TARGET_COUNT
        assert int((grid.row(i) == Value.EMPTY).sum()) == TARGET_COUNT
        assert int((grid.col(i) == Value.FULL).sum()) == TARGET_COUNT
        assert int((grid.col(i) == Value.EMPTY).sum()) == TARGET_COUNT


def test_many_generated_grids_are_all_valid():
    for seed in range(25):
        gen = LocalExpansionGenerator(rng=random.Random(seed))
        grid, _ = gen.generate()
        assert validate(grid).is_valid


def test_repair_heuristic_reduces_attempts_needed():
    """Proof-of-concept check for the design doc's open question: does the
    lookahead repair heuristic actually help convergence? Averaged over many
    seeds, generation with the heuristic on should need no more attempts than
    with it off."""
    n = 40
    with_heuristic = []
    without_heuristic = []
    for seed in range(n):
        gen_on = LocalExpansionGenerator(rng=random.Random(seed), use_repair_heuristic=True)
        _, stats_on = gen_on.generate()
        with_heuristic.append(stats_on.attempts)

        gen_off = LocalExpansionGenerator(rng=random.Random(seed), use_repair_heuristic=False)
        _, stats_off = gen_off.generate()
        without_heuristic.append(stats_off.attempts)

    avg_on = sum(with_heuristic) / n
    avg_off = sum(without_heuristic) / n
    assert avg_on <= avg_off
