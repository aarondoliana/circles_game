"""Archive: a collection of generated, validated, classified Puzzles, per
the design doc's object model. Puzzles are batch-generated offline (the
design doc explicitly calls out that generation doesn't need to be fast
since results get archived and pulled from at play time) and can be
persisted to/from a JSON file.

"Sorted ID based on complexity" is implemented as a live rank -- a puzzle's
position when the archive is sorted by difficulty -- rather than a value
baked into the Puzzle itself, since it's only meaningful relative to
whatever else is currently in the archive.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field

from generator import LocalExpansionGenerator
from masking import generate_puzzle
from puzzle import Puzzle
from solver import solve

TIER_NAMES = ("Easy", "Medium", "Hard", "Extra Hard")
# Easy and Medium each take a third of the archive by rank; the hardest
# third (fewest given cells / most solver guesses) splits evenly into Hard
# and Extra Hard.
TIER_WEIGHTS = (1, 1, 0.5, 0.5)


@dataclass
class Archive:
    puzzles: dict = field(default_factory=dict)  # puzzle_id -> Puzzle

    def add(self, puzzle: Puzzle) -> bool:
        """Adds `puzzle`; returns False without changing anything if a
        puzzle with the same id (same starting+solution grids) is already
        archived."""
        if puzzle.puzzle_id in self.puzzles:
            return False
        self.puzzles[puzzle.puzzle_id] = puzzle
        return True

    def __len__(self) -> int:
        return len(self.puzzles)

    def get(self, puzzle_id: str) -> Puzzle | None:
        return self.puzzles.get(puzzle_id)

    def sorted_by_complexity(self) -> list:
        """Easiest first: most given cells, then fewest solver guesses
        needed. A puzzle's index in this list is its "sorted ID."""
        return sorted(self.puzzles.values(), key=lambda p: (-p.given_cells, p.solve_guesses))

    def rank_of(self, puzzle_id: str) -> int | None:
        for rank, puzzle in enumerate(self.sorted_by_complexity()):
            if puzzle.puzzle_id == puzzle_id:
                return rank
        return None

    def difficulty_tier(self, puzzle_id: str) -> str | None:
        """Splits the archive by complexity rank according to TIER_WEIGHTS,
        so the labels stay meaningful as the archive grows instead of
        relying on hard-coded absolute thresholds."""
        rank = self.rank_of(puzzle_id)
        n = len(self)
        if rank is None or n == 0:
            return None
        total_weight = sum(TIER_WEIGHTS)
        cumulative = 0.0
        for name, weight in zip(TIER_NAMES, TIER_WEIGHTS):
            cumulative += weight
            if rank < n * cumulative / total_weight:
                return name
        return TIER_NAMES[-1]

    def puzzles_in_tier(self, tier: str) -> list:
        ordered = self.sorted_by_complexity()
        return [p for p in ordered if self.difficulty_tier(p.puzzle_id) == tier]

    def random_puzzle(self, rng: random.Random | None = None, tier: str | None = None) -> Puzzle | None:
        rng = rng or random.Random()
        pool = self.puzzles_in_tier(tier) if tier else list(self.puzzles.values())
        return rng.choice(pool) if pool else None

    def to_dict(self) -> dict:
        return {"puzzles": [p.to_dict() for p in self.puzzles.values()]}

    @classmethod
    def from_dict(cls, data: dict) -> "Archive":
        archive = cls()
        for puzzle_data in data["puzzles"]:
            archive.add(Puzzle.from_dict(puzzle_data))
        return archive

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f)

    @classmethod
    def load(cls, path: str) -> "Archive":
        with open(path) as f:
            return cls.from_dict(json.load(f))


# Cycled round-robin by generate_batch so an archive spans a real difficulty
# gradient rather than everything landing near the fully-minimized floor.
# Roughly mirrors the hand-tested Puzzle A/B/C specs from the masking demo:
# a relaxed many-givens puzzle, a spread-out medium one, and a minimized hard
# one.
DEFAULT_DIFFICULTY_PROFILES = (
    dict(target_n=26, minimize=False, full_fraction=0.5, spread="uniform"),
    dict(target_n=16, minimize=False, full_fraction=0.5, spread="spread"),
    dict(target_n=30, minimize=True, full_fraction=0.75, spread="spread"),
)


def generate_batch(count: int, rng: random.Random | None = None,
                    profiles=DEFAULT_DIFFICULTY_PROFILES,
                    masking_max_attempts: int = 200, archive: Archive | None = None) -> Archive:
    """Generates `count` new puzzles (skipping the rare exact-duplicate) and
    adds them to `archive` (a fresh one if not given), cycling through
    `profiles` (each a kwargs dict for masking.generate_puzzle) round-robin
    so the batch spans a real difficulty gradient rather than clustering at
    one masking setting."""
    rng = rng or random.Random()
    archive = archive if archive is not None else Archive()
    target_count = len(archive) + count
    profile_index = 0
    while len(archive) < target_count:
        profile = profiles[profile_index % len(profiles)]
        profile_index += 1
        solved, _ = LocalExpansionGenerator(rng=rng).generate()
        starting, _, mask_stats = generate_puzzle(
            solved, rng=rng, max_attempts=masking_max_attempts, **profile)
        if starting is None:
            continue
        _, solve_stats = solve(starting, limit=1, rng=rng)
        puzzle = Puzzle.create(starting, solved, given_cells=mask_stats.final_cells,
                                solve_guesses=solve_stats.guesses)
        archive.add(puzzle)
    return archive
