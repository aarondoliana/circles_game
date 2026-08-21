import random

from constants import Value
from generator import LocalExpansionGenerator
from grid import Grid
from masking import generate_puzzle
from solver import solve
from validator import validate


def test_inverted_swaps_full_and_empty():
    grid = Grid()
    grid.set(0, 0, Value.FULL)
    grid.set(0, 1, Value.EMPTY)
    inverted = grid.inverted()
    assert inverted.get(0, 0) == Value.EMPTY
    assert inverted.get(0, 1) == Value.FULL


def test_inverted_leaves_blank_cells_blank():
    grid = Grid()
    grid.set(0, 0, Value.FULL)
    inverted = grid.inverted()
    assert inverted.get(1, 1) == Value.BLANK


def test_inverted_is_its_own_inverse():
    solved, _ = LocalExpansionGenerator(rng=random.Random(0)).generate()
    assert (solved.inverted().inverted().cells == solved.cells).all()


def test_inverted_preserves_validity_and_unique_solution():
    solved, _ = LocalExpansionGenerator(rng=random.Random(1)).generate()
    starting, _, _ = generate_puzzle(solved, rng=random.Random(2))

    inverted_solved = solved.inverted()
    inverted_starting = starting.inverted()

    assert validate(inverted_solved).is_valid
    solutions, _ = solve(inverted_starting, limit=2)
    assert len(solutions) == 1
    assert (solutions[0].cells == inverted_solved.cells).all()
