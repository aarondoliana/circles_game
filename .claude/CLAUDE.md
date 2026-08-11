# Circles Game

## Project structure

One project, two halves, sharing a spec:

- **Root (Python)** — the game engine: generator, solver, validator, archive. Tests live in `tests/` (pytest).
- **`web/`** (TypeScript/React/Vite) — the player-facing client. Tests via `npm test` (vitest), lint via `npm run lint` (oxlint).

## Source of truth

- `specs/design_doc.md` is the project spec. **Agents must never modify files under `specs/`** — that directory is user-owned only. Read it for context, never edit it.
- `implementation_plan.md` (repo root, tracked in git — repo isn't public yet, revisit gitignoring it once it is) is the living working-memory file between agent and user: what's next, what's been completed, and backlog items that don't belong in the spec.
  - Check it at the start of a session to see what's next before asking the user or guessing.
  - Update it as work completes — mark tasks done, add newly-discovered follow-up tasks — without waiting to be asked.
  - This replaces the old `todos.md` (migrated and removed).

## Legacy / do not rely on

- `dev.ipynb` — scratch/dev notebook, not part of the maintained codebase.
- `iterative_algorithm_fail.xlsx` — abandoned experiment, reference only.

## Testing

- Always run relevant tests after making code changes, without waiting to be asked:
  - Python: `pytest` (root)
  - Web: `npm test` (in `web/`) — also run `npm run lint` for web changes.

## Git workflow

- Work on feature branches, not directly on `main`. Create a branch for non-trivial changes before committing.
- Use conventional commits for message subjects (`feat:`, `fix:`, `chore:`, `refactor:`, `test:`, `docs:`, etc.).
- The agent may commit at natural checkpoints (e.g. after completing a task from `implementation_plan.md`) without asking each time — this overrides the default "never commit unless asked" behavior for this repo. Still never push, force-push, or rewrite history without explicit approval.
– Never add "Co-Authored-By" or AI attribution lines to git commits.
– Do not include AI markers in pull request descriptions.

## Best practices

- Use type hints on new Python functions; keep TypeScript strictly typed in `web/` (avoid `any`).
- No speculative abstractions — prefer straightforward code over premature generalization or config flags, matching the project's existing approach (see `implementation_plan.md` backlog entries for examples of deferred complexity).
- Keep `specs/design_doc.md` and the implementation in sync conceptually: if implementation needs to diverge from or extend what the spec describes, flag it to the user rather than silently drifting, since agents can't edit `specs/` themselves.
- Background long-running processes (e.g. `npm run dev`, watch-mode test runners) rather than blocking the session on them.
