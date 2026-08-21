# Circles Game

A re-creation of the New York Times Magazine's circles/squares logic puzzle, with a Python
generator/solver engine and a React web client.

## The game

An 8x8 grid of cells, each holding a full circle (⚫), an empty circle (O), or blank. Starting
from a few pre-filled cells, fill in the rest so that:

- **R2.** Every row and every column ends up with exactly 4 full circles and 4 empty circles.
- **R3.** No three consecutive cells in a row or column read ⚫O⚫ or O⚫O (a circle can't be
  "squeezed between" two of the other kind).

Every archived puzzle has a unique solution reachable by these two rules alone (plus, for the
hardest puzzles, some guess-and-backtrack).

See `specs/design_doc.md` for the full design spec.

## Project structure

One project, two halves, sharing the spec above:

- **Root (Python)** — the game engine: `generator.py` (builds solved grids), `masking.py` (masks
  a solved grid down to a starting puzzle with a unique solution), `solver.py` (R2/R3 +
  brute-force line-solving + backtracking), `validator.py`, `puzzle.py`/`archive.py` (puzzle
  object model and difficulty classification), `export_archive.py` (CLI to batch-generate and
  export the puzzle pool the web client reads).
- **`web/`** (TypeScript/React/Vite) — the player-facing client, which loads a static
  `web/public/archive.json` at runtime (no backend).

## Playtesting the web app

```sh
cd web
npm install   # first time only
npm run dev
```

Then open the printed local URL (typically `http://localhost:5173`) in a browser.

**Controls:** click a cell to cycle blank → full → empty → blank. Givens (the puzzle's starting
cells) are locked. "New game" picks a random puzzle from the archive at the chosen difficulty
(Easy/Medium/Hard/Extra Hard). Other controls: Undo/Redo, Restart, Show/Hide solution, and a
"Live validation" toggle that highlights incorrect cells and R2/R3 rule violations as you play.

## Regenerating the puzzle archive

`web/public/archive.json` is a static snapshot, not a live connection to the Python engine — you
only need to regenerate it when you want a fresh or larger puzzle pool:

```sh
python3 export_archive.py --count 60 --seed 0
```

or, to guarantee a minimum number of puzzles per difficulty tier (slower, since the hardest tier
is rare — see `archive.generate_batch_to_quotas`):

```sh
python3 export_archive.py --quotas 30 30 30 20 --seed 0   # Easy Medium Hard "Extra Hard"
```

## Testing

```sh
pytest                       # Python engine tests (repo root)
cd web && npm test           # web client tests (vitest)
cd web && npm run lint       # web client lint (oxlint)
```

Run these after any code change in the relevant half of the project.

## Setup

```sh
pip install -r requirements.txt   # Python (numpy, pytest)
cd web && npm install             # web client
```
