import random

from archive import Archive, generate_batch
from generator import LocalExpansionGenerator
from puzzle import Puzzle
from solver import has_unique_solution, solve


def _dummy_puzzle(puzzle_id, given_cells, solve_guesses, grid):
    return Puzzle(puzzle_id=puzzle_id, starting=grid, solution=grid,
                  given_cells=given_cells, solve_guesses=solve_guesses)


def _some_grid():
    solved, _ = LocalExpansionGenerator(rng=random.Random(0)).generate()
    return solved


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
    archive.add(_dummy_puzzle("hard", given_cells=8, solve_guesses=20, grid=grid))
    archive.add(_dummy_puzzle("easy", given_cells=26, solve_guesses=0, grid=grid))
    archive.add(_dummy_puzzle("medium", given_cells=16, solve_guesses=5, grid=grid))

    ordered_ids = [p.puzzle_id for p in archive.sorted_by_complexity()]
    assert ordered_ids == ["easy", "medium", "hard"]


def test_rank_of_matches_sorted_position():
    grid = _some_grid()
    archive = Archive()
    archive.add(_dummy_puzzle("hard", given_cells=8, solve_guesses=20, grid=grid))
    archive.add(_dummy_puzzle("easy", given_cells=26, solve_guesses=0, grid=grid))

    assert archive.rank_of("easy") == 0
    assert archive.rank_of("hard") == 1
    assert archive.rank_of("missing") is None


def test_difficulty_tier_splits_into_four_tiers():
    grid = _some_grid()
    archive = Archive()
    # 12 puzzles, strictly decreasing given_cells -> increasing difficulty.
    # Easy/Medium each take a third (4 puzzles); the hardest third splits
    # evenly into Hard and Extra Hard (2 puzzles each).
    for i in range(12):
        archive.add(_dummy_puzzle(f"p{i}", given_cells=30 - i, solve_guesses=i, grid=grid))

    tiers = [archive.difficulty_tier(f"p{i}") for i in range(12)]
    assert tiers == ["Easy"] * 4 + ["Medium"] * 4 + ["Hard"] * 2 + ["Extra Hard"] * 2


def test_random_puzzle_respects_tier_filter():
    grid = _some_grid()
    archive = Archive()
    for i in range(12):
        archive.add(_dummy_puzzle(f"p{i}", given_cells=30 - i, solve_guesses=i, grid=grid))

    rng = random.Random(0)
    for _ in range(10):
        puzzle = archive.random_puzzle(rng=rng, tier="Extra Hard")
        assert archive.difficulty_tier(puzzle.puzzle_id) == "Extra Hard"


def test_save_and_load_round_trip(tmp_path):
    grid = _some_grid()
    archive = Archive()
    archive.add(_dummy_puzzle("a", given_cells=10, solve_guesses=1, grid=grid))
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


def test_generate_batch_spans_a_real_difficulty_gradient():
    # 6 puzzles cycles through all 3 default profiles (relaxed/medium/minimized)
    # at least once, so given_cells shouldn't all cluster near the minimized floor.
    archive = generate_batch(6, rng=random.Random(3))
    given_cells = sorted(p.given_cells for p in archive.puzzles.values())
    assert given_cells[-1] - given_cells[0] >= 8


def test_generate_batch_appends_to_existing_archive():
    archive = generate_batch(2, rng=random.Random(1))
    generate_batch(2, rng=random.Random(2), archive=archive)
    assert len(archive) == 4
