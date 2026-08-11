# Implementation plan

Working memory between agent and user: what's next, what's been completed, and backlog items that don't belong in `specs/design_doc.md` (which stays a clear, end-state-oriented spec). Tracked in git for now, since the repo isn't public yet.

## Now / Next

**Next session: open by interviewing the user** on MVP scope — what "done" looks like across generator/solver, the Hint provider, and web client polish — so this Now/Next section and the Backlog priority order can be set with their input rather than assumed.

### Done (2026-08-11): solver.py brute-force-line-solving refactor, finished + fixed

Picks up from the 2026-07-27→08-10 VSCode session (decision confirmed with user 2026-07-30: solver search-space reduction order is `R2 > R3 > brute-force-line-solving > recursive backtracking`). The in-progress refactor had a stale reference (`solver.py:185` still called the removed `find_gap_forced_moves`, breaking `pytest` collection) — fixed, and along the way two design issues surfaced and were resolved with the user:

1. **Propagation order didn't match the stated hierarchy.** `propagate()` was interleaving R3 → line-solving → R2 every pass instead of draining R2+R3 to a fixpoint *before* ever running line-solving. Since line-solving is a strict superset of what R2/R3 can force, running it earlier meant it silently claimed cells R2/R3 alone could have solved — which would have made a "did this puzzle need line-solving" difficulty signal untrustworthy. Fixed: `propagate()` now drains R2+R3 to a combined fixpoint first, only then runs one line-solving pass, looping back to R2/R3 if that made progress.
2. **Added `SolveStats.line_solving_uses`**, incremented once per `propagate()` pass where line-solving contributed a move (now gated correctly per point 1, so it only counts genuine escalations beyond R2/R3). Not yet wired through `Puzzle`/`archive.py` the way `solve_guesses` is — natural follow-up once puzzle-difficulty classification is actually being built (see "Solver pattern naming, deferred to the Hint provider" below).
3. **Consolidated R2/R3 duplication.** `validator.py` now exposes the shared primitives (`count_full_empty`, `is_alternating_triplet`, `line_violates_r2`, `line_violates_r3`); `solver.py` imports and reuses them instead of re-deriving the same rules in three separate places, removing drift risk.

All 46 tests pass (`pytest`). Not yet committed — pending user go-ahead.

_(nothing else in flight — add tasks here as they're picked up)_

## Backlog

### Archive expansion via inversion

The archive can be cheaply doubled by inverting circle types throughout a Puzzle's starting and solution grids (⚫↔O). R2 (count balance) and R3 (squeeze pattern) both depend only on equality relationships between cells, not on which value is which, so an inverted Puzzle is automatically valid and uniquely solvable at the same difficulty tier -- no re-solving or re-classification needed.

Worth doing once a tier's pool is small enough that the avoid-repeat fallback (`unsolvedPuzzles` in `web/src/player/playerArchive.ts`) starts serving noticeable repeats.

### Solver pattern naming, deferred to the Hint provider

Decided approach for the Solver's search-space reduction, per `specs/design_doc.md`'s Algorithm section: R2 > R3 > brute-force-line-solving > recursive backtracking, with backtracking reserved for complex inter-line dependencies that brute-force-line-solving can't resolve on its own. The solver itself doesn't need the specific named configurations drafted in the design doc's "Additional solver patterns" list (group-of-three, quintuplet, adjacency inference, etc.) individually hand-coded -- a generic brute-force pass over each line's blank-cell assignments against R2/R3 subsumes all of them.

Revisit the named patterns when we build the Hint provider: exhaustively enumerate what brute-force-line-solving actually covers, then generalize/organize those configurations by complexity and logical entailment (which patterns are special cases of others) so hints can be offered in a sensible learn-easiest-first order.

**Why dedicated patterns matter later even though the solver doesn't need them:** tracking which named patterns get used during a solve (once they exist) is a more natural difficulty signal than raw stats alone -- a mix of (A) number of starting given circles, (B) the distribution of which solving patterns were needed, and (C) number of backtracking attempts (implying how much of the puzzle depends on complex inter-line dependencies rather than local reasoning).

### Hint provider

Not yet designed or implemented. Deferred until after the solver work above -- the named pattern enumeration/generalization happens as part of building this.

### Solve stats: hint disaggregation/exclusion

`specs/design_doc.md`'s "Solve stats" section calls for stats disaggregated by whether hints were used, and for "free hints mode" puzzles to be excluded from stats -- neither is implemented (`web/src/player/playerArchive.ts`'s `recordSolveTime`/`timeStatsFor`), since the Hint provider above doesn't exist yet. The Show Solution exclusion is already in place (`solutionEverRevealed` in `web/src/game/gameSession.ts`). Revisit once hints ship.

### Split "reveal errors on a completed grid" into its own opt-in, tracked like hints

Today, live validation (`GridView.tsx`'s `cell--incorrect`/`cell--rule-violation` highlighting, gated by `state.liveValidation` in `gameSession.ts`) also fires once the grid is fully filled in (`showValidation = !solutionRevealed && (state.liveValidation || isComplete)`). On a complete-but-wrong grid, this highlights exactly the cells that are wrong -- which for an 8x8 grid with few wrong cells is close to just handing over the solution.

This should become a separate toggle from live-validation-during-play (e.g. "highlight errors on a completed grid"), off by default. When it's on, treat that puzzle attempt like the "learning mode" / hints-used case for stats purposes: exclude it from clean solve-time stats, the same way `solutionEverRevealed` already excludes Show-Solution attempts (see the "Solve stats: hint disaggregation/exclusion" item above -- this option should plug into the same mechanism once it exists).

### Interaction polish

Keyboard and right-click controls for the web client, kept separate from the Player/Archive layer work by agreement. Not yet started.
