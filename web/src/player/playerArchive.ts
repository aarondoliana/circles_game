// The Player + Player Archive from the design doc, scoped to what a fully
// static client can do: an anonymous player ID and a solved-puzzle record,
// both persisted to localStorage (no accounts/backend yet -- see the
// architecture decisions from the Game-layer session). Storage is injected
// (defaulting to window.localStorage) so this stays testable without a DOM.
import type { ArchivedPuzzle, Difficulty } from "../game/types";

const STORAGE_KEY = "circles-game:player-v1";
const DIFFICULTIES: Difficulty[] = ["Easy", "Medium", "Hard", "Extra Hard"];

export interface SolvedRecord {
  difficulty: Difficulty;
  solvedAt: number; // epoch ms of the *first* solve
}

export interface PlayerArchiveState {
  playerId: string;
  solved: Record<string, SolvedRecord>; // puzzleId -> record
}

export type PlayerStats = {
  total: number;
  byDifficulty: Record<Difficulty, number>;
};

export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

function generatePlayerId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return `player-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function createPlayerArchive(): PlayerArchiveState {
  return { playerId: generatePlayerId(), solved: {} };
}

export function loadPlayerArchive(storage: StorageLike = window.localStorage): PlayerArchiveState {
  const raw = storage.getItem(STORAGE_KEY);
  if (!raw) return createPlayerArchive();
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed.playerId !== "string" || typeof parsed.solved !== "object") {
      return createPlayerArchive();
    }
    return parsed as PlayerArchiveState;
  } catch {
    return createPlayerArchive();
  }
}

export function savePlayerArchive(state: PlayerArchiveState, storage: StorageLike = window.localStorage): void {
  storage.setItem(STORAGE_KEY, JSON.stringify(state));
}

/** First-solve wins: re-solving an already-recorded puzzle is a no-op. */
export function recordSolved(state: PlayerArchiveState, puzzleId: string, difficulty: Difficulty): PlayerArchiveState {
  if (puzzleId in state.solved) return state;
  return {
    ...state,
    solved: { ...state.solved, [puzzleId]: { difficulty, solvedAt: Date.now() } },
  };
}

export function isSolved(state: PlayerArchiveState, puzzleId: string): boolean {
  return puzzleId in state.solved;
}

export function statsFor(state: PlayerArchiveState): PlayerStats {
  const byDifficulty = Object.fromEntries(DIFFICULTIES.map((d) => [d, 0])) as Record<Difficulty, number>;
  for (const record of Object.values(state.solved)) {
    byDifficulty[record.difficulty] += 1;
  }
  return { total: Object.keys(state.solved).length, byDifficulty };
}

/** Puzzles this player hasn't solved yet, falling back to the full pool if
 * every puzzle passed in has already been solved -- so puzzle selection
 * never dead-ends once a pool is exhausted. */
export function unsolvedPuzzles(state: PlayerArchiveState, puzzles: ArchivedPuzzle[]): ArchivedPuzzle[] {
  const remaining = puzzles.filter((p) => !isSolved(state, p.id));
  return remaining.length > 0 ? remaining : puzzles;
}
