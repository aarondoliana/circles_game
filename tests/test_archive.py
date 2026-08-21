import random

import pytest

from archive import Archive, _maybe_invert_colors, generate_batch, generate_batch_to_quotas
from generator import LocalExpansionGenerator
from puzzle import Puzzle
from solver import has_unique_solution, solve


def _dummy_puzzle(puzzle_id, given_cells, solve_guesses, grid, line_solving_uses=0):
    return Puzzle(puzzle_id=puzzle_id, starting=grid, solution=grid,
                  given_cells=given_cells, solve_guesses=solve_guesses,
                  line_solving_uses=line_solving_uses)


def _some_grid():
    solved, _ = LocalExpansionGenerator(rng=random.Random(0)).generate()
    return solved


class _FixedCoin:
    """A plain (non-random.Random) stand-in exposing just .random(), for
    deterministically forcing/blocking _maybe_invert_colors's coin flip.
    Deliberately NOT a random.Random subclass: overriding .random() there
    makes CPython's Random.__init_subclass__ re-route _randbelow (and so
    randint/shuffle/sample) through .random() too, which would corrupt
    everything else generation needs randomness for -- this helper is only
    ever handed to the one function that calls nothing but .random()."""

    def __init__(self, value):
        self._value = value

    def random(self):
        return self._value


def test_add_dedups_by_puzzle_id():
    grid = _some_grid()
    archive = Archive()
    puzzle = _dummy_puzzle("abc", given_cells=10, solve_guesses=0, grid=grid)

    assert archive.add(puzzle) is True
    assert archive.add(puzzle) is False
    assert len(archive) == 1


def test_sorted_by_complexity_is_easiest_first():
    grid = _some_grid()
    archive = Archive()
    archive.add(_dummy_puzzle("hard", given_cells=8, solve_guesses=0, line_solving_uses=1, grid=grid))
    archive.add(_dummy_puzzle("easy", given_cells=26, solve_guesses=0, line_solving_uses=0, grid=grid))
    archive.add(_dummy_puzzle("medium", given_cells=16, solve_guesses=0, line_solving_uses=1, grid=grid))

    ordered_ids = [p.puzzle_id for p in archive.sorted_by_complexity()]
    assert ordered_ids == ["easy", "medium", "hard"]


def test_rank_of_matches_sorted_position():
    grid = _some_grid()
    archive = Archive()
    archive.add(_dummy_puzzle("hard", given_cells=8, solve_guesses=20, line_solving_uses=3, grid=grid))
    archive.add(_dummy_puzzle("easy", given_cells=26, solve_guesses=0, line_solving_uses=0, grid=grid))

    assert archive.rank_of("easy") == 0
    assert archive.rank_of("hard") == 1
    assert archive.rank_of("missing") is None


def test_difficulty_tier_classifies_by_solve_effort():
    grid = _some_grid()
    archive = Archive()

    # Easy: solvable by pure R2/R3 (no line-solving, no backtracking).
    archive.add(_dummy_puzzle("e1", given_cells=26, solve_guesses=0, line_solving_uses=0, grid=grid))
    archive.add(_dummy_puzzle("e2", given_cells=22, solve_guesses=0, line_solving_uses=0, grid=grid))

    # Needs line-solving but no backtracking -> the Medium/Hard band, split
    # by relative given_cells rank within the band (top half = Medium).
    archive.add(_dummy_puzzle("m1", given_cells=20, solve_guesses=0, line_solving_uses=1, grid=grid))
    archive.add(_dummy_puzzle("m2", given_cells=18, solve_guesses=0, line_solving_uses=2, grid=grid))
    archive.add(_dummy_puzzle("h1", given_cells=12, solve_guesses=0, line_solving_uses=1, grid=grid))
    archive.add(_dummy_puzzle("h2", given_cells=10, solve_guesses=0, line_solving_uses=3, grid=grid))

    # Extra Hard: needed at least one grid-level backtracking guess, even
    # when given_cells (15) falls inside the Medium/Hard band's range --
    # effort, not given_cells, is the deciding factor.
    archive.add(_dummy_puzzle("x1", given_cells=15, solve_guesses=1, line_solving_uses=2, grid=grid))
    archive.add(_dummy_puzzle("x2", given_cells=9, solve_guesses=3, line_solving_uses=4, grid=grid))

    assert archive.difficulty_tier("e1") == "Easy"
    assert archive.difficulty_tier("e2") == "Easy"
    assert archive.difficulty_tier("m1") == "Medium"
    assert archive.difficulty_tier("m2") == "Medium"
    assert archive.difficulty_tier("h1") == "Hard"
    assert archive.difficulty_tier("h2") == "Hard"
    assert archive.difficulty_tier("x1") == "Extra Hard"
    assert archive.difficulty_tier("x2") == "Extra Hard"


def test_random_puzzle_respects_tier_filter():
    grid = _some_grid()
    archive = Archive()
    archive.add(_dummy_puzzle("e1", given_cells=26, solve_guesses=0, line_solving_uses=0, grid=grid))
    archive.add(_dummy_puzzle("m1", given_cells=18, solve_guesses=0, line_solving_uses=1, grid=grid))
    archive.add(_dummy_puzzle("x1", given_cells=9, solve_guesses=2, line_solving_uses=3, grid=grid))
    archive.add(_dummy_puzzle("x2", given_cells=7, solve_guesses=4, line_solving_uses=5, grid=grid))

    rng = random.Random(0)
    for _ in range(10):
        puzzle = archive.random_puzzle(rng=rng, tier="Extra Hard")
        assert archive.difficulty_tier(puzzle.puzzle_id) == "Extra Hard"


def test_save_and_load_round_trip(tmp_path):
    grid = _some_grid()
    archive = Archive()
    archive.add(_dummy_puzzle("a", given_cells=10, solve_guesses=1, line_solving_uses=2, grid=grid))
    archive.add(_dummy_puzzle("b", given_cells=20, solve_guesses=0, grid=grid))

    path = tmp_path / "archive.json"
    archive.save(str(path))
    restored = Archive.load(str(path))

    assert len(restored) == 2
    assert restored.get("a").given_cells == 10
    assert (restored.get("b").starting.cells == grid.cells).all()


def test_generate_batch_produces_valid_unique_puzzles():
    archive = generate_batch(4, rng=random.Random(42))
    assert len(archive) == 4

    for puzzle in archive.puzzles.values():
        assert has_unique_solution(puzzle.starting)
        solutions, _ = solve(puzzle.starting, limit=1)
        assert (solutions[0].cells == puzzle.solution.cells).all()


def test_maybe_invert_colors_inverts_below_half():
    grid = _some_grid()
    starting, solved = _maybe_invert_colors(grid, grid, _FixedCoin(0.0))
    assert (starting.cells == grid.inverted().cells).all()
    assert (solved.cells == grid.inverted().cells).all()


def test_maybe_invert_colors_keeps_at_or_above_half():
    grid = _some_grid()
    starting, solved = _maybe_invert_colors(grid, grid, _FixedCoin(0.99))
    assert (starting.cells == grid.cells).all()
    assert (solved.cells == grid.cells).all()


def test_generate_batch_spans_a_real_difficulty_gradient():
    # 8 puzzles cycles through all 4 default profiles (relaxed x2/medium/minimized)
    # at least once, so given_cells shouldn't all cluster near the minimized floor.
    archive = generate_batch(8, rng=random.Random(3))
    given_cells = sorted(p.given_cells for p in archive.puzzles.values())
    assert given_cells[-1] - given_cells[0] >= 8


def test_generate_batch_appends_to_existing_archive():
    archive = generate_batch(2, rng=random.Random(1))
    generate_batch(2, rng=random.Random(2), archive=archive)
    assert len(archive) == 4


def test_tier_counts_matches_puzzles_in_tier():
    archive = generate_batch(12, rng=random.Random(5))
    counts = archive.tier_counts()
    assert sum(counts.values()) == len(archive)
    for tier in ("Easy", "Medium", "Hard", "Extra Hard"):
        assert counts[tier] == len(archive.puzzles_in_tier(tier))


def test_generate_batch_to_quotas_meets_minimums():
    quotas = {"Easy": 3, "Medium": 3, "Hard": 3, "Extra Hard": 2}
    archive = generate_batch_to_quotas(quotas, rng=random.Random(9))

    counts = archive.tier_counts()
    for tier, minimum in quotas.items():
        assert counts[tier] >= minimum


def test_generate_batch_to_quotas_appends_to_existing_archive():
    archive = generate_batch(4, rng=random.Random(1))
    starting_len = len(archive)

    generate_batch_to_quotas({"Easy": 3}, rng=random.Random(2), archive=archive)
    assert len(archive) >= starting_len
    assert archive.tier_counts()["Easy"] >= 3


def test_generate_batch_to_quotas_raises_when_quota_unreachable_in_time():
    with pytest.raises(RuntimeError):
        generate_batch_to_quotas({"Extra Hard": 1000}, rng=random.Random(0), max_draws=3)
