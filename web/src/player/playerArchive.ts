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

/** One qualifying completed attempt. Unlike SolvedRecord, every qualifying
 * completion appends a new sample (including repeats of the same puzzle) so
 * time stats improve with play. Callers exclude disqualified attempts
 * (Show Solution used, and eventually "free hints mode") before recording. */
export interface SolveTimeRecord {
  difficulty: Difficulty;
  durationMs: number;
  solvedAt: number;
}

export interface PlayerArchiveState {
  playerId: string;
  solved: Record<string, SolvedRecord>; // puzzleId -> record
  times: SolveTimeRecord[];
}

export type PlayerStats = {
  total: number;
  byDifficulty: Record<Difficulty, number>;
};

export interface DifficultyTimeStats {
  count: number;
  bestMs: number;
  averageMs: number;
  bestAverageMs: number; // inter-quartile mean
}

export type TimeStats = Record<Difficulty, DifficultyTimeStats | null>;

export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

function generatePlayerId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return `player-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function createPlayerArchive(): PlayerArchiveState {
  return { playerId: generatePlayerId(), solved: {}, times: [] };
}

export function loadPlayerArchive(storage: StorageLike = window.localStorage): PlayerArchiveState {
  const raw = storage.getItem(STORAGE_KEY);
  if (!raw) return createPlayerArchive();
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed.playerId !== "string" || typeof parsed.solved !== "object") {
      return createPlayerArchive();
    }
    // `times` backfilled for archives saved before solve-time tracking existed.
    return { times: [], ...parsed } as PlayerArchiveState;
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

/** Records one qualifying solve-time sample. The caller decides whether this
 * attempt qualifies (e.g. Show Solution wasn't used). */
export function recordSolveTime(state: PlayerArchiveState, difficulty: Difficulty, durationMs: number): PlayerArchiveState {
  return {
    ...state,
    times: [...state.times, { difficulty, durationMs, solvedAt: Date.now() }],
  };
}

function average(values: number[]): number {
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

/** Mean of the middle 50% of values (trimmed by count, not exact quartile
 * interpolation) -- a "typical" time that isn't skewed by one lucky or one
 * fumbled attempt. */
function interQuartileMean(values: number[]): number {
  const sorted = [...values].sort((a, b) => a - b);
  const trim = Math.floor(sorted.length / 4);
  return average(sorted.slice(trim, sorted.length - trim));
}

export function timeStatsFor(state: PlayerArchiveState): TimeStats {
  const result = {} as TimeStats;
  for (const difficulty of DIFFICULTIES) {
    const durations = state.times.filter((t) => t.difficulty === difficulty).map((t) => t.durationMs);
    result[difficulty] =
      durations.length === 0
        ? null
        : {
            count: durations.length,
            bestMs: Math.min(...durations),
            averageMs: average(durations),
            bestAverageMs: interQuartileMean(durations),
          };
  }
  return result;
}
