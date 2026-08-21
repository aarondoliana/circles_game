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
from grid import Grid
from masking import generate_puzzle
from puzzle import Puzzle
from solver import solve

TIER_NAMES = ("Easy", "Medium", "Hard", "Extra Hard")


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

    def _classified(self) -> list:
        """Returns (Puzzle, tier_name) pairs, easiest first, per the design
        doc's "Difficulty levels of puzzles" section: solve *effort* is the
        primary classifier, not given_cells alone -- a puzzle's given_cells
        and the solving power actually needed to crack it turn out to be
        fairly independent (e.g. plenty of 20-given-cell puzzles still need
        brute-force line-solving), so a fixed given_cells range can't carry
        the whole classification on its own.

        Three effort buckets, cheapest first:
        - Easy: solvable by R2/R3 alone (no line-solving, no backtracking).
        - "needs line-solving, no backtracking": splits into Medium/Hard by
          relative given_cells rank *within this band* (more given cells =
          easier = Medium), rather than a fixed threshold, so the split
          stays meaningful as the archive's generation profiles change.
        - Extra Hard: needed at least one grid-level backtracking guess.
        """
        easy = sorted(
            (p for p in self.puzzles.values() if p.solve_guesses == 0 and p.line_solving_uses == 0),
            key=lambda p: (-p.given_cells, p.solve_guesses))
        band = sorted(
            (p for p in self.puzzles.values() if p.solve_guesses == 0 and p.line_solving_uses > 0),
            key=lambda p: (-p.given_cells, p.line_solving_uses))
        extra_hard = sorted(
            (p for p in self.puzzles.values() if p.solve_guesses > 0),
            key=lambda p: (-p.given_cells, p.solve_guesses))

        midpoint = (len(band) + 1) // 2  # Medium gets the extra puzzle on odd-sized bands
        medium, hard = band[:midpoint], band[midpoint:]

        return (
            [(p, "Easy") for p in easy]
            + [(p, "Medium") for p in medium]
            + [(p, "Hard") for p in hard]
            + [(p, "Extra Hard") for p in extra_hard]
        )

    def sorted_by_complexity(self) -> list:
        """Easiest first, per `_classified`'s effort-based ordering. A
        puzzle's index in this list is its "sorted ID.\""""
        return [puzzle for puzzle, _ in self._classified()]

    def rank_of(self, puzzle_id: str) -> int | None:
        for rank, puzzle in enumerate(self.sorted_by_complexity()):
            if puzzle.puzzle_id == puzzle_id:
                return rank
        return None

    def difficulty_tier(self, puzzle_id: str) -> str | None:
        for puzzle, tier in self._classified():
            if puzzle.puzzle_id == puzzle_id:
                return tier
        return None

    def puzzles_in_tier(self, tier: str) -> list:
        return [puzzle for puzzle, t in self._classified() if t == tier]

    def tier_counts(self) -> dict:
        """Puzzle count per tier, from a single `_classified()` pass -- use
        this instead of calling `puzzles_in_tier` once per tier when all
        four counts are needed together."""
        counts = {name: 0 for name in TIER_NAMES}
        for _, tier in self._classified():
            counts[tier] += 1
        return counts

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
# gradient. Each profile's `target_n_range` gives given_cells variety within
# the profile rather than every draw landing on one fixed number; `target_n`
# itself is resolved from that range per-draw (see `_resolve_profile`).
# Tuned empirically against the solver's actual effort signals (not just
# given_cells) per the design doc's "Difficulty levels of puzzles" section:
# - (24, 30) unminimized lands "solvable by pure R2/R3" (Easy) ~55% of the
#   time, with the rest spilling into the line-solving band -- listed twice
#   below so Easy isn't starved relative to the other tiers, which all get
#   contributions from every profile.
# - (14, 20) unminimized lands in the line-solving band the vast majority of
#   the time (few pure-R2/R3 draws that high).
# - Aggressive minimization from n=30 pushes given_cells down to ~7-11 and is
#   the only regime that reliably produces grid-level backtracking (Extra
#   Hard) -- confirmed empirically to occur in ~5-20% of draws here, so Extra
#   Hard is a real, populated (if intentionally rare) tier rather than a
#   hypothetical one.
DEFAULT_DIFFICULTY_PROFILES = (
    dict(target_n_range=(24, 30), minimize=False, full_fraction=0.5, spread="uniform"),
    dict(target_n_range=(24, 30), minimize=False, full_fraction=0.5, spread="uniform"),
    dict(target_n_range=(14, 20), minimize=False, full_fraction=0.5, spread="spread"),
    dict(target_n=30, minimize=True, full_fraction=0.75, spread="spread"),
)


# Which DEFAULT_DIFFICULTY_PROFILES entry is most likely to produce a given
# tier, for generate_batch_to_quotas's targeted top-up. Medium and Hard
# share a profile: both come from the same "needs line-solving, no
# backtracking" band, and Archive._classified always splits that band
# ~50/50 by rank regardless of the given_cells values feeding it -- so
# there's no way to grow one without the other, and no need to try.
TIER_PROFILES = {
    "Easy": DEFAULT_DIFFICULTY_PROFILES[0],
    "Medium": DEFAULT_DIFFICULTY_PROFILES[2],
    "Hard": DEFAULT_DIFFICULTY_PROFILES[2],
    "Extra Hard": DEFAULT_DIFFICULTY_PROFILES[3],
}


def _resolve_profile(profile: dict, rng: random.Random) -> dict:
    """Expands a profile's `target_n_range` (if present) into a concrete
    `target_n` drawn fresh from that range."""
    profile = dict(profile)
    n_range = profile.pop("target_n_range", None)
    if n_range is not None:
        profile["target_n"] = rng.randint(*n_range)
    return profile


def _maybe_invert_colors(starting: Grid, solved: Grid, rng: random.Random) -> tuple:
    """50/50 color-reverses (starting, solved) -- see Grid.inverted -- to
    cancel out any FULL/EMPTY sampling bias baked into masking's
    `full_fraction` (several DEFAULT_DIFFICULTY_PROFILES entries skew toward
    FULL givens) rather than letting it leak into the archive as a whole,
    per the design doc's generator notes. Puzzles have color-reversing
    symmetry: R2/R3 only depend on equality between cells, not on which
    value is which, so this doesn't change validity, uniqueness, given_cells,
    or solve effort."""
    if rng.random() < 0.5:
        return starting.inverted(), solved.inverted()
    return starting, solved


def _draw_puzzle(profile: dict, rng: random.Random, masking_max_attempts: int) -> Puzzle | None:
    """Generates one candidate Puzzle from `profile` (a masking.generate_puzzle
    kwargs dict, optionally with `target_n_range`), or None if masking
    couldn't find a unique-solution mask within `masking_max_attempts`."""
    resolved = _resolve_profile(profile, rng)
    solved, _ = LocalExpansionGenerator(rng=rng).generate()
    starting, _, mask_stats = generate_puzzle(
        solved, rng=rng, max_attempts=masking_max_attempts, **resolved)
    if starting is None:
        return None

    starting, solved = _maybe_invert_colors(starting, solved, rng)

    _, solve_stats = solve(starting, limit=1, rng=rng)
    return Puzzle.create(starting, solved, given_cells=mask_stats.final_cells,
                          solve_guesses=solve_stats.guesses,
                          line_solving_uses=solve_stats.line_solving_uses)


def generate_batch(count: int, rng: random.Random | None = None,
                    profiles=DEFAULT_DIFFICULTY_PROFILES,
                    masking_max_attempts: int = 200, archive: Archive | None = None) -> Archive:
    """Generates `count` new puzzles (skipping the rare exact-duplicate) and
    adds them to `archive` (a fresh one if not given), cycling through
    `profiles` (each a kwargs dict for masking.generate_puzzle, optionally
    using `target_n_range` instead of a fixed `target_n`) round-robin so the
    batch spans a real difficulty gradient rather than clustering at one
    masking setting."""
    rng = rng or random.Random()
    archive = archive if archive is not None else Archive()
    target_count = len(archive) + count
    profile_index = 0
    while len(archive) < target_count:
        puzzle = _draw_puzzle(profiles[profile_index % len(profiles)], rng, masking_max_attempts)
        profile_index += 1
        if puzzle is not None:
            archive.add(puzzle)
    return archive


def generate_batch_to_quotas(min_counts: dict, rng: random.Random | None = None,
                              archive: Archive | None = None,
                              masking_max_attempts: int = 200, max_draws: int = 20000) -> Archive:
    """Generates puzzles until every tier named in `min_counts` (e.g.
    `{"Easy": 30, "Extra Hard": 20}`) has at least that many archived, adding
    them to `archive` (a fresh one if not given).

    Unlike `generate_batch`'s fixed round-robin, each draw targets whichever
    tier is currently furthest below its quota (via `TIER_PROFILES`), so
    draws aren't wasted on tiers that are already satisfied. This matters
    most for Extra Hard: it only ever comes from the minimize profile, and
    only ~5-20% of that profile's draws actually need backtracking, so
    round-robin sampling alone leaves it badly underrepresented at any
    archive size big enough to fill the other tiers comfortably.

    Raises RuntimeError if `max_draws` is exhausted before every quota is
    met -- a sign a quota is unreachable at the current DEFAULT_DIFFICULTY_PROFILES
    settings rather than something to retry silently.
    """
    rng = rng or random.Random()
    archive = archive if archive is not None else Archive()

    for _ in range(max_draws):
        counts = archive.tier_counts()
        deficits = {tier: quota - counts.get(tier, 0) for tier, quota in min_counts.items()}
        worst_tier = max(deficits, key=deficits.get)
        if deficits[worst_tier] <= 0:
            return archive
        puzzle = _draw_puzzle(TIER_PROFILES[worst_tier], rng, masking_max_attempts)
        if puzzle is not None:
            archive.add(puzzle)

    remaining = {tier: deficit for tier, deficit in deficits.items() if deficit > 0}
    raise RuntimeError(
        f"generate_batch_to_quotas: quotas not met after {max_draws} draws; still short: {remaining}")
