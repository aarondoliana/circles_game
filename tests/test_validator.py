from constants import Value
from grid import Grid
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


def test_design_doc_solution_is_valid():
    grid = Grid.from_values(SOLVED_EXAMPLE)
    result = validate(grid)
    assert result.is_valid, result


def test_r2_violation_detected_for_too_many_full_in_a_row():
    values = [row[:] for row in SOLVED_EXAMPLE]
    values[0] = [FULL, FULL, FULL, FULL, FULL, EMPTY, EMPTY, EMPTY]
    result = validate(Grid.from_values(values))
    assert not result.is_valid
    assert "row 0" in result.r2_violations


def test_r3_violation_detected_for_alternating_triplet():
    values = [row[:] for row in SOLVED_EXAMPLE]
    values[0][0:3] = [FULL, EMPTY, FULL]
    result = validate(Grid.from_values(values))
    assert not result.is_valid
    assert "row 0" in result.r3_violations


def test_r3_allows_a_run_of_three_of_the_same_kind():
    values = [row[:] for row in SOLVED_EXAMPLE]
    # positions 3,4,5 of row 0 are already EMPTY,EMPTY,EMPTY in SOLVED_EXAMPLE
    result = validate(Grid.from_values(values))
    assert "row 0" not in result.r3_violations


def test_blank_cells_are_ignored():
    values = [[BLANK] * 8 for _ in range(8)]
    result = validate(Grid.from_values(values))
    assert result.is_valid
