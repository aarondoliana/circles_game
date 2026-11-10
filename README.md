# Circles Game

A re-creation of the New York Times Magazine's circles/squares logic puzzle: a Python
generator/solver engine that produces puzzles with a *guaranteed unique solution* and a
calibrated difficulty rating, paired with a React web client to play them.

The interesting engineering is mostly on the generation side — see
[Design highlights](#design-highlights) below.

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

## Design highlights

- **Generation works backward from a solved grid.** `generator.py` builds a complete, valid
  solution first (random local expansion, re-validated against R2/R3 as it grows); `masking.py`
  then blanks cells down to a starting puzzle, using `solver.has_unique_solution` to reject any
  mask that doesn't converge to exactly one solution. A final greedy pass removes further cells
  one at a time while uniqueness holds, pushing each puzzle toward the fewest givens its
  particular draw can support.
- **The solver mirrors how a person actually plays**, in a strict escalation order — R2 (row/column
  counts) → R3 (no three-in-a-row) → brute-force line-solving (enumerate every valid completion of
  a line, keep the cells where all of them agree) → grid-wide backtracking, only as a last resort.
  That ordering isn't just elegant; it's load-bearing: because the engine only reaches for
  backtracking when local reasoning truly runs out, *which* techniques a solve needed becomes a
  trustworthy per-puzzle difficulty signal, not a heuristic guess.
- **Difficulty tiers are classified by solve effort, not just cell count.** Early iterations ranked
  puzzles by givens alone, but empirically that doesn't track how a puzzle actually feels to
  solve — plenty of puzzles with the same number of givens need very different amounts of
  reasoning. Tiers are now primarily split by *what the solver needed* (R2/R3 alone vs.
  line-solving vs. backtracking), calibrated against real playtesting.
- **A cheap symmetry keeps the puzzle pool unbiased.** R2 and R3 only depend on relationships
  between cells, not which value is which — so a puzzle with every circle swapped (⚫↔O) is exactly
  as valid, unique, and difficult as the original (`Grid.inverted()`). Generation uses this to
  randomly color-reverse about half of each batch, canceling out any FULL/EMPTY skew introduced
  during sampling, and the same trick can cheaply double the archive later if needed.

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

## License

MIT — see [LICENSE](LICENSE).
