"""CLI: batch-generate an Archive and export it as the static JSON the web
client fetches at runtime (web/public/archive.json). Re-run this whenever
the web app needs a fresh/larger puzzle pool -- it's a snapshot, not a live
connection to the Python pipeline (the client is fully static, no backend).
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from archive import TIER_NAMES, generate_batch, generate_batch_to_quotas

DEFAULT_OUTPUT = Path(__file__).parent / "web" / "public" / "archive.json"


def export_archive(seed: int, output: Path, count: int | None = None, quotas: dict | None = None) -> None:
    """Generates an Archive either by fixed `count` (round-robin profiles,
    fast but doesn't guarantee any particular tier is well-represented) or
    by per-tier `quotas` (targeted top-up, slower but guarantees minimums --
    see `archive.generate_batch_to_quotas`). Exactly one of the two must be
    given."""
    rng = random.Random(seed)
    if quotas is not None:
        archive = generate_batch_to_quotas(quotas, rng=rng)
    else:
        archive = generate_batch(count, rng=rng)
    puzzles = [
        {
            "id": puzzle.puzzle_id,
            "startingGrid": puzzle.starting.cells.tolist(),
            "solutionGrid": puzzle.solution.cells.tolist(),
            "givenCells": puzzle.given_cells,
            "difficulty": archive.difficulty_tier(puzzle.puzzle_id),
        }
        for puzzle in archive.sorted_by_complexity()
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"puzzles": puzzles}))
    print(f"wrote {len(puzzles)} puzzles to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--count", type=int, help="number of puzzles to generate via round-robin profiles")
    group.add_argument("--quotas", type=int, nargs=4, metavar=("EASY", "MEDIUM", "HARD", "EXTRA_HARD"),
                        help="minimum puzzle count per tier via targeted top-up generation "
                             "(archive.generate_batch_to_quotas); overrides --count")
    parser.add_argument("--seed", type=int, default=0, help="RNG seed, for reproducible exports")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="output JSON path")
    args = parser.parse_args()

    if args.quotas is not None:
        export_archive(args.seed, args.output, quotas=dict(zip(TIER_NAMES, args.quotas)))
    else:
        export_archive(args.seed, args.output, count=args.count or 16)
