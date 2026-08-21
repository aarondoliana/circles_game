# Implementation plan

Working memory between agent and user: what's next, what's been completed, and backlog items that don't belong in `specs/design_doc.md` (which stays a clear, end-state-oriented spec). Tracked in git for now, since the repo isn't public yet.

## Now / Next

### MVP scope, finalized with user (2026-08-19)

"Done" for this version means a playable link solid enough to share with friends/family — not full design-doc feature completeness (Hint provider, Player/Platform accounts, etc.). Confirmed with the user:

- **Hint provider:** deferred to a later version, not MVP-blocking.
- **Pre-existing backlog items** (archive expansion via inversion, interaction polish, solve-stats disaggregation, configurable grid size) are not MVP-blocking; they stay in the Backlog section below at their existing priority, un-elevated.
- **New must-have, not previously in the design doc: a daily puzzle per difficulty tier, plus past-puzzle navigation, so the archive can't be "exhausted."** Confirmed with the user: the same puzzle for every player on a given day per tier (shared daily challenge, Wordle-style), the web client stays backend-free (per its current architecture) rather than introducing a server, and past puzzles stay browsable indefinitely (no rolling-window expiry).
- No hard deadline; paced by available time.

### Next up: design the daily-puzzle mechanism

Not yet designed — this is new scope, not in `specs/design_doc.md` (which only describes "a random Puzzle... from the Archive" selection; the user should update the doc once this is designed, since agents can't edit `specs/`). Current puzzle selection (`web/src/App.tsx`'s `pickPuzzle`) is pure random-from-pool with an avoid-repeat fallback (`unsolvedPuzzles` in `playerArchive.ts`) — nothing date-driven exists yet. Open questions to resolve with the user before implementing:

1. **Date -> puzzle mapping.** Likely a deterministic index derived from days-since-epoch (e.g. a launch date) mod the tier's archive size, so past dates are always recomputable client-side (no separate storage needed for "past" puzzles) and no backend is required. Needs an explicit epoch/launch date once decided.
2. **Timezone.** Is "today" the player's local calendar day, or a fixed UTC cutover (matters for players near midnight, and for whether "the same puzzle for everyone" is strictly true worldwide)?
3. **Wraparound.** A finite per-tier pool means a pure modulo mapping eventually repeats once days-since-epoch exceeds pool size. "Won't exhaust the future archive" most plausibly means "always has a puzzle ready for tomorrow," not "literally infinite, never-repeating" -- worth confirming explicitly, since it changes how urgently pool size / regeneration cadence matters. The "Archive expansion via inversion" backlog item (cheap 2x pool size per tier) and periodic `export_archive.py --quotas` regeneration (this session's mechanism) both extend runway before any wraparound is felt.
4. **UI for past-puzzle navigation.** Not yet designed (calendar picker? prev/next day buttons? a list?).

### Done (2026-08-19): color-reversal debiasing added to generation

User's own addition to `specs/design_doc.md`'s generator notes (alongside the daily-puzzle doc update above): puzzles have color-reversing symmetry, so color-reversing puzzles ~half the time before archiving cancels out any FULL/EMPTY sampling bias baked into masking's `full_fraction` (several `DEFAULT_DIFFICULTY_PROFILES` entries skew toward FULL givens, e.g. 0.75) rather than letting it leak into the archive as a whole. Flagged by the user as cheap and worth folding into MVP scope.

1. **`Grid.inverted()`** (`grid.py`): swaps FULL/EMPTY everywhere, leaves BLANK as BLANK. R2/R3 only depend on equality between cells, not on which value is which, so an inverted grid is valid/uniquely-solvable/same-difficulty iff the original is (same reasoning already used by the "Archive expansion via inversion" backlog item, applied here to debias rather than to grow the pool).
2. **`archive._maybe_invert_colors(starting, solved, rng)`**: 50/50 coin flip, applied in `_draw_puzzle` right after masking succeeds (before solving/classifying, so `solve_stats` reflects the grid actually stored). Deliberately factored out as its own function rather than inlined -- a `rng.random() < 0.5` inline call turned out to be untestable in isolation (see next point), so pulling it out let the coin-flip logic be tested directly instead.
3. **Testing pitfall worth remembering:** initially tried to test this by subclassing `random.Random` and overriding just `.random()` to force the coin flip deterministically. This silently corrupted *all* other randomness in the same draw (mask sampling, solver guess order) -- CPython's `Random.__init_subclass__` detects a subclass overriding `.random()` and re-routes `_randbelow` (and so `randint`/`shuffle`/`sample`) through it too, rather than the normal `getrandbits`-backed path. Fixed by testing `_maybe_invert_colors` directly with a plain non-`Random` duck-typed stub exposing only `.random()`, not a `Random` subclass.
4. Regenerated `web/public/archive.json` again with the same `--quotas 30 30 30 20 --seed 0` (167 total puzzles: Easy 30 / Medium 59 / Hard 58 / Extra Hard 20). Verified the debiasing worked: given-cell FULL/EMPTY split across the archive is 48.9%/51.1%, close to even.

All 56 Python tests (`pytest`) and 39 web tests (`npm test`) pass; `npm run lint` clean. Not yet committed — pending user go-ahead.

### Done (2026-08-18): difficulty tiers recalibrated post-playtest, effort-based classification

User playtested the current puzzle pool and updated `specs/design_doc.md`'s "Difficulty levels of puzzles" section with new tier definitions based on that experience. Implemented to match, after conferring on calibration ambiguities (the doc's given-cell ranges overlap across tiers, e.g. Easy 17-24 vs Medium 12-18):

1. **`Puzzle` gained a `line_solving_uses` field** (`puzzle.py`), plumbed from `Solver.SolveStats.line_solving_uses` through `Archive.generate_batch` — previously only `given_cells`/`solve_guesses` were persisted.
2. **`Archive.difficulty_tier`/`sorted_by_complexity` rewritten to be effort-primary, not a percentile split of given_cells.** Confirmed with the user: solve-effort category is the main classifier (Easy = solvable by pure R2/R3; Extra Hard = needed grid-level backtracking; Medium/Hard = needed line-solving but no backtracking, split by *relative* given_cells rank within that shared-effort band rather than a fixed threshold). Empirically, given_cells alone doesn't predict effort well (e.g. most 20-given-cell puzzles still needed line-solving), so a fixed-range classifier would have contradicted the doc's own effort descriptions for many puzzles. `TIER_WEIGHTS` (the old percentile-split constant) removed as dead code.
3. **Confirmed empirically that grid-level backtracking (Extra Hard) is reachable** — the design doc had flagged this as an open question ("it remains to be seen if this even exists"). It occurs in ~5-20% of aggressively-minimized draws depending on RNG, so Extra Hard is a real, if intentionally rare, tier.
4. **Retuned `DEFAULT_DIFFICULTY_PROFILES`** (`archive.py`) — the old 3 fixed-`target_n` profiles (26/16/30-minimized) only ever produced 3 discrete given_cells values and didn't reliably populate the new tier bands. Now 4 profiles round-robin, two skewed toward Easy (`target_n_range=(24,30)`, unminimized) to avoid Easy being starved relative to the other tiers, one skewed toward the line-solving band (`target_n_range=(14,20)`), one aggressive-minimization profile for Hard/Extra Hard. `target_n_range` is a new profile option (resolved per-draw via `_resolve_profile`) alongside the existing fixed `target_n`.
5. First regeneration of `web/public/archive.json` (60 puzzles, seed 0) came out Extra-Hard-thin (2 puzzles) since round-robin only routes 1/4 of draws to the one profile that can produce it, and only ~5-20% of *those* succeed. User flagged this and asked for a fix rather than accepting the thin tier.
6. **Added `Archive.generate_batch_to_quotas`** (`archive.py`): instead of round-robin, each draw targets whichever tier is currently furthest below a given per-tier minimum (`TIER_PROFILES` maps each tier to the `DEFAULT_DIFFICULTY_PROFILES` entry most likely to produce it), so draws aren't wasted on tiers already satisfied. Medium and Hard intentionally share a profile -- `_classified()` always splits their shared band ~50/50 by rank regardless of which given_cells values feed it, so there's no way to target one without the other. Draw logic factored out of `generate_batch` into a shared `_draw_puzzle` helper to avoid duplicating it. Raises `RuntimeError` if `max_draws` (default 20000) is exhausted without meeting every quota, rather than silently returning short. `export_archive.py` gained a `--quotas EASY MEDIUM HARD EXTRA_HARD` CLI flag (mutually exclusive with `--count`) to drive it.
7. Regenerated `web/public/archive.json` for real with `--quotas 30 30 30 20 --seed 0` (~65s, 185 total puzzles) — final split Easy 30 / Medium 68 / Hard 67 / Extra Hard 20. Notably, 3 of the 30 Easy puzzles have very few given cells (10, 15, 15) but happen to be solvable by pure R2/R3 alone -- a real if rare case, and a good confirmation that effort-primary classification (point 2 above) does the right thing where a given_cells-only classifier would have mislabeled them Hard.

All 50 Python tests (`pytest`) and 39 web tests (`npm test`) pass; `npm run lint` clean. Not yet committed — pending user go-ahead.

_(nothing else in flight — add tasks here as they're picked up)_

## Backlog

### Archive expansion via inversion

The archive can be cheaply doubled by inverting circle types throughout a Puzzle's starting and solution grids (⚫↔O). R2 (count balance) and R3 (squeeze pattern) both depend only on equality relationships between cells, not on which value is which, so an inverted Puzzle is automatically valid and uniquely solvable at the same difficulty tier -- no re-solving or re-classification needed.

Worth doing once a tier's pool is small enough that the avoid-repeat fallback (`unsolvedPuzzles` in `web/src/player/playerArchive.ts`) starts serving noticeable repeats.

### Solver pattern naming, deferred to the Hint provider

Decided approach for the Solver's search-space reduction, per `specs/design_doc.md`'s Algorithm section: R2 > R3 > brute-force-line-solving > recursive backtracking, with backtracking reserved for complex inter-line dependencies that brute-force-line-solving can't resolve on its own. The solver itself doesn't need the specific named configurations drafted in the design doc's "Additional solver patterns" list (group-of-three, quintuplet, adjacency inference, etc.) individually hand-coded -- a generic brute-force pass over each line's blank-cell assignments against R2/R3 subsumes all of them.

Revisit the named patterns when we build the Hint provider: exhaustively enumerate what brute-force-line-solving actually covers, then generalize/organize those configurations by complexity and logical entailment (which patterns are special cases of others) so hints can be offered in a sensible learn-easiest-first order.

**Why dedicated patterns matter later even though the solver doesn't need them:** tracking which named patterns get used during a solve (once they exist) is a more natural difficulty signal than raw stats alone -- a mix of (A) number of starting given circles, (B) the distribution of which solving patterns were needed, and (C) number of backtracking attempts (implying how much of the puzzle depends on complex inter-line dependencies rather than local reasoning). (B)/(C) are now used at the coarse pass/fail level (`line_solving_uses > 0`, `solve_guesses > 0`) for the difficulty tiers implemented 2026-08-18 above; per-pattern granularity is still the Hint provider's job.

### Hint provider

Not yet designed or implemented. Deferred until after the solver work above -- the named pattern enumeration/generalization happens as part of building this.

### Solve stats: hint disaggregation/exclusion

`specs/design_doc.md`'s "Solve stats" section calls for stats disaggregated by whether hints were used, and for "free hints mode" puzzles to be excluded from stats -- neither is implemented (`web/src/player/playerArchive.ts`'s `recordSolveTime`/`timeStatsFor`), since the Hint provider above doesn't exist yet. The Show Solution exclusion is already in place (`solutionEverRevealed` in `web/src/game/gameSession.ts`). Revisit once hints ship.

### Split "reveal errors on a completed grid" into its own opt-in, tracked like hints

Today, live validation (`GridView.tsx`'s `cell--incorrect`/`cell--rule-violation` highlighting, gated by `state.liveValidation` in `gameSession.ts`) also fires once the grid is fully filled in (`showValidation = !solutionRevealed && (state.liveValidation || isComplete)`). On a complete-but-wrong grid, this highlights exactly the cells that are wrong -- which for an 8x8 grid with few wrong cells is close to just handing over the solution.

This should become a separate toggle from live-validation-during-play (e.g. "highlight errors on a completed grid"), off by default. When it's on, treat that puzzle attempt like the "learning mode" / hints-used case for stats purposes: exclude it from clean solve-time stats, the same way `solutionEverRevealed` already excludes Show-Solution attempts (see the "Solve stats: hint disaggregation/exclusion" item above -- this option should plug into the same mechanism once it exists).

### Interaction polish

Keyboard and right-click controls for the web client, kept separate from the Player/Archive layer work by agreement. Not yet started.

### Configurable grid size (10x10, 12x12, ...)

User request (2026-08-19): let players choose a board size, e.g. 10x10 with 5 FULL/5 EMPTY per row/column, or 12x12 with 6/6, alongside the current 8x8. Not yet designed or scoped -- flagged here as a placeholder.

A decent starting point: both engines already centralize the board dimension in one constant rather than hard-coding 8 everywhere (`constants.py`'s `SIZE`/`TARGET_COUNT = SIZE // 2` on the Python side, `web/src/game/types.ts`'s `SIZE` on the web side), so the core R2/R3/line-solving/backtracking logic likely generalizes with little change. Real open questions, not yet discussed with the user:

- **Puzzle/Archive schema:** puzzles don't currently carry a board size -- `Puzzle`/`archive.json` would need a size field, and the difficulty-tier calibration (given_cells ranges, `DEFAULT_DIFFICULTY_PROFILES`) is tuned for 8x8 specifically and would need separate tuning per size (a 10x10's "Easy" given-cell count isn't the 8x8 one).
- **Web selection UI:** `Controls.tsx`'s difficulty picker (and `App.tsx`'s `pickPuzzle`) would need a size dimension alongside difficulty; `GridView.tsx`'s CSS grid layout assumes a fixed cell size against an 8x8 board.
- **Player archive/stats:** `playerArchive.ts`'s solved-tracking and time stats are keyed by difficulty only -- would need to decide whether stats are also split by board size or pooled.
- **Solver cost at larger sizes:** brute-force line-solving enumerates up to C(SIZE, TARGET_COUNT) completions per line (70 at SIZE=8); C(12,6)=924 is still cheap, so this is likely a non-issue, but worth confirming empirically before committing.
