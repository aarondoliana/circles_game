# TODOs

Open threads that don't belong in `specs/design_doc.md` (which stays a clear, end-state-oriented spec).

## Archive expansion via inversion

The archive can be cheaply doubled by inverting circle types throughout a Puzzle's starting and solution grids (⚫↔O). R2 (count balance) and R3 (squeeze pattern) both depend only on equality relationships between cells, not on which value is which, so an inverted Puzzle is automatically valid and uniquely solvable at the same difficulty tier -- no re-solving or re-classification needed.

Worth doing once a tier's pool is small enough that the avoid-repeat fallback (`unsolvedPuzzles` in `web/src/player/playerArchive.ts`) starts serving noticeable repeats.

## Augmented solver deduction patterns

`specs/design_doc.md` has draft patterns 1, 3, and 4 (in addition to the existing pattern 2) for the solver's "additional patterns" section, written but not yet implemented in `generator.py`/the solver code. Implement and test these once we pick this back up.

## Hint provider

Not yet designed or implemented. Deferred until after the solver deduction patterns above.

## Solve stats: hint disaggregation/exclusion

`specs/design_doc.md`'s "Solve stats" section calls for stats disaggregated by whether hints were used, and for "free hints mode" puzzles to be excluded from stats -- neither is implemented (`web/src/player/playerArchive.ts`'s `recordSolveTime`/`timeStatsFor`), since the Hint provider above doesn't exist yet. The Show Solution exclusion is already in place (`solutionEverRevealed` in `web/src/game/gameSession.ts`). Revisit once hints ship.

## Interaction polish

Keyboard and right-click controls for the web client, kept separate from the Player/Archive layer work by agreement. Not yet started.
