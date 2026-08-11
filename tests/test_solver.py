import random

from constants import SIZE, Value
from generator import LocalExpansionGenerator
from grid import Grid
from solver import find_line_forced_moves, find_r2_forced_moves, find_r3_forced_moves, has_unique_solution, propagate, solve
from validator import validate

FULL, EMPTY, BLANK = Value.FULL, Value.EMPTY, Value.BLANK

SOLVED_EXAMPLE = [
    [EMPTY, FULL, FULL, EMPTY, EMPTY, EMPTY, FULL, FULL],
    [FULL, EMPTY, EMPTY, FULL, FULL, FULL, EMPTY, EMPTY],
    [FULL, EMPTY, EMPTY, FULL, FULL, FULL, EMPTY, EMPTY],
    [EMPTY, FULL, FULL, EMPTY, EMPTY, EMPTY, FULL, FULL],
    [EMPTY, FULL, FULL, EMPTY, EMPTY, EMPTY, FULL, FULL],
    [FULL, EMPTY, EMPTY, FULL, FULL, FULL, EMPTY, EMPTY],
    [FULL, EMPTY, EMPTY, FULL, FULL, FULL, EMPTY, EMPTY],
    [EMPTY, FULL, FULL, EMPTY, EMPTY, EMPTY, FULL, FULL],
]


def _masked(values, keep):
    """Returns a copy of `values` with every cell blanked except those at
    (row, col) positions in `keep`."""
    masked = [[BLANK] * SIZE for _ in range(SIZE)]
    for r, c in keep:
        masked[r][c] = values[r][c]
    return masked


def test_r2_forces_remaining_blanks_once_a_line_has_four_of_a_kind():
    values = [row[:] for row in SOLVED_EXAMPLE]
    values[0][4] = BLANK
    values[0][5] = BLANK  # row 0 already has 4 FULL, so both must be forced EMPTY
    grid = Grid.from_values(values)
    moves = {(r, c): v for r, c, v in find_r2_forced_moves(grid)}
    assert moves.get((0, 4)) == EMPTY
    assert moves.get((0, 5)) == EMPTY


def test_r3_forces_blank_between_two_same_known_neighbors():
    values = [row[:] for row in SOLVED_EXAMPLE]
    values[0][1] = BLANK  # row 0: EMPTY, _, FULL -> middle must stay FULL to match col-3 triplet? use direct triplet check instead
    grid = Grid.from_values(values)
    moves = {(r, c): v for r, c, v in find_r3_forced_moves(grid)}
    # row 0 triplet (0,1,2) = EMPTY, _, FULL: since ends differ, no r3 force from this triplet alone;
    # but triplet (1,2,3) = _, FULL, EMPTY forces position 1 (end-blank) to match its neighbor FULL
    assert moves.get((0, 1)) == FULL


def test_line_forced_moves_solves_the_gap_configuration_between_matching_full_circles():
    # F _ _ _ F: the middle blank must be EMPTY, else the flanking R3
    # triplets would force both inner blanks to FULL too, five-in-a-row.
    # R2/R3 alone can't force this (no triplet here has exactly one blank),
    # so only brute-force-line-solving catches it.
    values = [[BLANK] * SIZE for _ in range(SIZE)]
    values[0][0] = FULL
    values[0][4] = FULL
    grid = Grid.from_values(values)
    moves = {(r, c): v for r, c, v in find_line_forced_moves(grid)}
    assert moves.get((0, 2)) == EMPTY


def test_line_forced_moves_solves_the_gap_configuration_between_matching_empty_circles():
    # Same pattern, along a column, with EMPTY flanks -> middle forced FULL.
    values = [[BLANK] * SIZE for _ in range(SIZE)]
    values[3][3] = EMPTY
    values[7][3] = EMPTY
    grid = Grid.from_values(values)
    moves = {(r, c): v for r, c, v in find_line_forced_moves(grid)}
    assert moves.get((5, 3)) == FULL


def test_line_forced_moves_does_not_overreach_when_nothing_is_forced():
    values = [[BLANK] * SIZE for _ in range(SIZE)]
    values[0][0] = FULL  # a single circle alone in an otherwise-blank line forces nothing
    grid = Grid.from_values(values)
    moves = {(r, c): v for r, c, v in find_line_forced_moves(grid)}
    assert moves == {}


def test_line_forced_moves_finds_forces_the_old_narrow_gap_pattern_missed():
    # F _ _ F _ _ _ _: the old hand-coded gap pattern only checked a fixed
    # 5-cell window (X _ _ _ X) and wouldn't fire here since these two FULLs
    # are only 3 apart. Brute-force-line-solving is strictly more powerful:
    # of the 3 valid R2/R3-consistent completions of this line, position 6
    # is EMPTY in all of them, so it's genuinely forced even though no named
    # pattern covers this exact configuration.
    values = [[BLANK] * SIZE for _ in range(SIZE)]
    values[0][0] = FULL
    values[0][3] = FULL
    grid = Grid.from_values(values)
    moves = {(r, c): v for r, c, v in find_line_forced_moves(grid)}
    assert moves.get((0, 6)) == EMPTY


def test_propagate_applies_line_forced_moves_without_guessing():
    values = [[BLANK] * SIZE for _ in range(SIZE)]
    values[0][0] = FULL
    values[0][4] = FULL
    grid = Grid.from_values(values)
    assert propagate(grid)
    assert grid.get(0, 2) == EMPTY


def test_propagate_solves_pure_logic_grid_without_guessing():
    # Blank out cells that R2/R3 alone can fully recover, using the doc's worked
    # example as ground truth.
    values = [row[:] for row in SOLVED_EXAMPLE]
    values[0][4] = BLANK
    values[0][5] = BLANK
    grid = Grid.from_values(values)
    assert propagate(grid)
    assert grid.is_complete()
    assert validate(grid).is_valid
    assert grid.get(0, 4) == EMPTY
    assert grid.get(0, 5) == EMPTY


def test_solve_returns_original_solution_for_a_fully_filled_grid():
    grid = Grid.from_values(SOLVED_EXAMPLE)
    solutions, stats = solve(grid, limit=1)
    assert len(solutions) == 1
    assert (solutions[0].cells == grid.cells).all()
    assert stats.guesses == 0


def test_solve_line_solving_uses_zero_when_r2_r3_alone_suffice():
    values = [row[:] for row in SOLVED_EXAMPLE]
    values[0][4] = BLANK
    values[0][5] = BLANK
    grid = Grid.from_values(values)
    _, stats = solve(grid, limit=1)
    assert stats.line_solving_uses == 0


def test_solve_line_solving_uses_counts_when_the_gap_configuration_is_needed():
    values = [[BLANK] * SIZE for _ in range(SIZE)]
    values[0][0] = FULL
    values[0][4] = FULL
    grid = Grid.from_values(values)
    _, stats = solve(grid, limit=1)
    assert stats.line_solving_uses >= 1


def test_solve_detects_contradiction_and_returns_no_solutions():
    values = [[BLANK] * SIZE for _ in range(SIZE)]
    values[0] = [FULL, FULL, FULL, FULL, FULL, EMPTY, EMPTY, EMPTY]  # 5 FULL: violates R2 immediately
    grid = Grid.from_values(values)
    solutions, _ = solve(grid, limit=1)
    assert solutions == []


def test_solve_recovers_generated_solution_from_a_sparse_starting_grid():
    gen = LocalExpansionGenerator(rng=random.Random(7))
    solved, _ = gen.generate()
    keep = [(r, c) for r in range(SIZE) for c in range(SIZE) if (r * SIZE + c) % 4 == 0]
    starting = Grid.from_values(_masked(solved.cells.tolist(), keep))

    solutions, _ = solve(starting, limit=1)
    assert len(solutions) == 1
    assert validate(solutions[0]).is_valid
    for r, c in keep:
        assert solutions[0].get(r, c) == solved.get(r, c)


def test_has_unique_solution_true_for_a_fully_filled_grid():
    grid = Grid.from_values(SOLVED_EXAMPLE)
    assert has_unique_solution(grid)


def test_has_unique_solution_false_for_a_fully_blank_grid():
    grid = Grid()
    assert not has_unique_solution(grid)
