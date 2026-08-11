"""Validator for R2 (row/column count balance) and R3 (no alternating triplet).

The line-level primitives here (`count_full_empty`, `is_alternating_triplet`,
`line_violates_r2`, `line_violates_r3`) are the single source of truth for
what R2/R3 mean at the line/triplet level. `solver.py` imports and reuses
them directly (for its R2/R3 forced-move search and for brute-force
line-solving) rather than re-deriving the rules, so the rule definitions
can't drift out of sync between the validator and the solver.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

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


def count_full_empty(line: np.ndarray) -> tuple[int, int]:
    """Returns (count of FULL cells, count of EMPTY cells) in a row/column --
    the shared primitive behind R2's count-balance rule."""
    return int(np.count_nonzero(line == Value.FULL)), int(np.count_nonzero(line == Value.EMPTY))


def is_alternating_triplet(a: Value, b: Value, c: Value) -> bool:
    """True if a-b-c forms the forbidden ⚫O⚫/O⚫O pattern -- R3's atomic
    violation check: the two ends match but the middle doesn't."""
    return a == c and a != b


def line_violates_r2(line: np.ndarray) -> bool:
    full, empty = count_full_empty(line)
    return full > TARGET_COUNT or empty > TARGET_COUNT


def line_violates_r3(line: Sequence[Value]) -> bool:
    """Accepts either a row/column `np.ndarray` or a plain list of `Value`
    (solver.py's brute-force line-solving calls this against trial
    completions built as plain lists)."""
    for i in range(SIZE - 2):
        a, b, c = line[i], line[i + 1], line[i + 2]
        if Value.BLANK in (a, b, c):
            continue
        if is_alternating_triplet(a, b, c):
            return True
    return False


def validate(grid: Grid) -> ValidationResult:
    result = ValidationResult()
    for r in range(SIZE):
        if line_violates_r2(grid.row(r)):
            result.r2_violations.append(f"row {r}")
        if line_violates_r3(grid.row(r)):
            result.r3_violations.append(f"row {r}")
    for c in range(SIZE):
        if line_violates_r2(grid.col(c)):
            result.r2_violations.append(f"col {c}")
        if line_violates_r3(grid.col(c)):
            result.r3_violations.append(f"col {c}")
    return result
