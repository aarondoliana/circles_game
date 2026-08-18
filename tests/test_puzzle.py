import random

from generator import LocalExpansionGenerator
from masking import generate_puzzle
from puzzle import Puzzle
from solver import solve


def _make_puzzle(seed):
    solved, _ = LocalExpansionGenerator(rng=random.Random(seed)).generate()
    starting, _, mask_stats = generate_puzzle(solved, rng=random.Random(seed * 3))
    _, solve_stats = solve(starting, limit=1)
    return Puzzle.create(starting, solved, given_cells=mask_stats.final_cells, solve_guesses=solve_stats.guesses,
                          line_solving_uses=solve_stats.line_solving_uses)


def test_create_is_deterministic_for_identical_grids():
    solved, _ = LocalExpansionGenerator(rng=random.Random(1)).generate()
    starting, _, _ = generate_puzzle(solved, rng=random.Random(11))

    a = Puzzle.create(starting, solved, given_cells=8, solve_guesses=0, line_solving_uses=0)
    b = Puzzle.create(starting.copy(), solved.copy(), given_cells=8, solve_guesses=0, line_solving_uses=0)
    assert a.puzzle_id == b.puzzle_id


def test_create_differs_for_different_puzzles():
    p1 = _make_puzzle(1)
    p2 = _make_puzzle(2)
    assert p1.puzzle_id != p2.puzzle_id


def test_to_dict_from_dict_round_trip():
    puzzle = _make_puzzle(4)
    restored = Puzzle.from_dict(puzzle.to_dict())

    assert restored.puzzle_id == puzzle.puzzle_id
    assert restored.given_cells == puzzle.given_cells
    assert restored.solve_guesses == puzzle.solve_guesses
    assert restored.line_solving_uses == puzzle.line_solving_uses
    assert (restored.starting.cells == puzzle.starting.cells).all()
    assert (restored.solution.cells == puzzle.solution.cells).all()
