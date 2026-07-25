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

from archive import generate_batch

DEFAULT_OUTPUT = Path(__file__).parent / "web" / "public" / "archive.json"


def export_archive(count: int, seed: int, output: Path) -> None:
    archive = generate_batch(count, rng=random.Random(seed))
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
    parser.add_argument("--count", type=int, default=16, help="number of puzzles to generate")
    parser.add_argument("--seed", type=int, default=0, help="RNG seed, for reproducible exports")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="output JSON path")
    args = parser.parse_args()
    export_archive(args.count, args.seed, args.output)
