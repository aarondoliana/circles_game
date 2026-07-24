"""Validator for R2 (row/column count balance) and R3 (no alternating triplet)."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from constants import SIZE, TARGET_COUNT, Value
from grid import Grid


@dataclass
class ValidationResult:
    r2_violations: list = field(default_factory=list)
    r3_violations: list = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.r2_violations and not self.r3_violations


def _line_violates_r2(line: np.ndarray) -> bool:
    full = int(np.count_nonzero(line == Value.FULL))
    empty = int(np.count_nonzero(line == Value.EMPTY))
    return full > TARGET_COUNT or empty > TARGET_COUNT


def _line_violates_r3(line: np.ndarray) -> bool:
    for i in range(SIZE - 2):
        a, b, c = line[i], line[i + 1], line[i + 2]
        if Value.BLANK in (a, b, c):
            continue
        if a == c and a != b:
            return True
    return False


def validate(grid: Grid) -> ValidationResult:
    result = ValidationResult()
    for r in range(SIZE):
        if _line_violates_r2(grid.row(r)):
            result.r2_violations.append(f"row {r}")
        if _line_violates_r3(grid.row(r)):
            result.r3_violations.append(f"row {r}")
    for c in range(SIZE):
        if _line_violates_r2(grid.col(c)):
            result.r2_violations.append(f"col {c}")
        if _line_violates_r3(grid.col(c)):
            result.r3_violations.append(f"col {c}")
    return result
