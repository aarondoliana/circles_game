import { describe, expect, it } from "vitest";
import type { ArchivedPuzzle } from "../../game/types";
import {
  createPlayerArchive,
  isSolved,
  loadPlayerArchive,
  recordSolved,
  recordSolveTime,
  savePlayerArchive,
  statsFor,
  timeStatsFor,
  unsolvedPuzzles,
  type PlayerArchiveState,
  type StorageLike,
} from "../playerArchive";

function fakeStorage(): StorageLike {
  const data = new Map<string, string>();
  return {
    getItem: (key) => data.get(key) ?? null,
    setItem: (key, value) => void data.set(key, value),
  };
}

function puzzle(id: string, difficulty: ArchivedPuzzle["difficulty"]): ArchivedPuzzle {
  return { id, difficulty, givenCells: 10, startingGrid: [] as never, solutionGrid: [] as never };
}

describe("createPlayerArchive / generatePlayerId", () => {
  it("creates distinct player ids each time", () => {
    const a = createPlayerArchive();
    const b = createPlayerArchive();
    expect(a.playerId).not.toBe(b.playerId);
    expect(a.solved).toEqual({});
  });
});

describe("loadPlayerArchive / savePlayerArchive", () => {
  it("creates a fresh archive when storage is empty", () => {
    const state = loadPlayerArchive(fakeStorage());
    expect(state.playerId).toBeTruthy();
    expect(state.solved).toEqual({});
  });

  it("round-trips through storage", () => {
    const storage = fakeStorage();
    let state = createPlayerArchive();
    state = recordSolved(state, "p1", "Easy");
    savePlayerArchive(state, storage);

    const restored = loadPlayerArchive(storage);
    expect(restored).toEqual(state);
  });

  it("falls back to a fresh archive on corrupt JSON", () => {
    const storage = fakeStorage();
    storage.setItem("circles-game:player-v1", "{not json");
    const state = loadPlayerArchive(storage);
    expect(state.solved).toEqual({});
  });

  it("falls back to a fresh archive on well-formed but wrong-shaped JSON", () => {
    const storage = fakeStorage();
    storage.setItem("circles-game:player-v1", JSON.stringify({ foo: "bar" }));
    const state = loadPlayerArchive(storage);
    expect(state.solved).toEqual({});
  });

  it("backfills a missing times array from before solve-time tracking existed", () => {
    const storage = fakeStorage();
    storage.setItem(
      "circles-game:player-v1",
      JSON.stringify({ playerId: "p1", solved: { p1: { difficulty: "Easy", solvedAt: 1 } } }),
    );
    const state = loadPlayerArchive(storage);
    expect(state.times).toEqual([]);
    expect(state.solved.p1.difficulty).toBe("Easy");
  });
});

describe("recordSolved / isSolved", () => {
  it("records a puzzle as solved", () => {
    const state = recordSolved(createPlayerArchive(), "p1", "Hard");
    expect(isSolved(state, "p1")).toBe(true);
    expect(isSolved(state, "p2")).toBe(false);
    expect(state.solved.p1.difficulty).toBe("Hard");
  });

  it("keeps the first solve time on repeat solves", () => {
    let state = recordSolved(createPlayerArchive(), "p1", "Hard");
    const firstSolvedAt = state.solved.p1.solvedAt;
    state = recordSolved(state, "p1", "Hard");
    expect(state.solved.p1.solvedAt).toBe(firstSolvedAt);
  });
});

describe("statsFor", () => {
  it("tallies solved counts per difficulty", () => {
    let state: PlayerArchiveState = createPlayerArchive();
    state = recordSolved(state, "p1", "Easy");
    state = recordSolved(state, "p2", "Easy");
    state = recordSolved(state, "p3", "Extra Hard");

    const stats = statsFor(state);
    expect(stats.total).toBe(3);
    expect(stats.byDifficulty).toEqual({ Easy: 2, Medium: 0, Hard: 0, "Extra Hard": 1 });
  });
});

describe("unsolvedPuzzles", () => {
  const pool = [puzzle("p1", "Easy"), puzzle("p2", "Easy"), puzzle("p3", "Easy")];

  it("excludes already-solved puzzles", () => {
    const state = recordSolved(createPlayerArchive(), "p1", "Easy");
    const remaining = unsolvedPuzzles(state, pool);
    expect(remaining.map((p) => p.id)).toEqual(["p2", "p3"]);
  });

  it("falls back to the full pool once everything is solved", () => {
    let state = createPlayerArchive();
    for (const p of pool) state = recordSolved(state, p.id, p.difficulty);
    const remaining = unsolvedPuzzles(state, pool);
    expect(remaining).toEqual(pool);
  });
});

describe("recordSolveTime / timeStatsFor", () => {
  it("accumulates every sample, including repeats of the same puzzle", () => {
    let state = createPlayerArchive();
    state = recordSolveTime(state, "Easy", 1000);
    state = recordSolveTime(state, "Easy", 2000);
    expect(state.times).toHaveLength(2);
  });

  it("returns null for a difficulty with no samples", () => {
    const stats = timeStatsFor(createPlayerArchive());
    expect(stats.Easy).toBeNull();
  });

  it("computes count/best/average per difficulty", () => {
    let state = createPlayerArchive();
    state = recordSolveTime(state, "Easy", 3000);
    state = recordSolveTime(state, "Easy", 1000);
    state = recordSolveTime(state, "Easy", 2000);

    const stats = timeStatsFor(state);
    expect(stats.Easy).toEqual({ count: 3, bestMs: 1000, averageMs: 2000, bestAverageMs: 2000 });
  });

  it("the inter-quartile mean resists an outlier that skews the plain average", () => {
    let state = createPlayerArchive();
    for (const seconds of [1, 2, 3, 4, 5, 6, 7, 100]) {
      state = recordSolveTime(state, "Hard", seconds * 1000);
    }
    const stats = timeStatsFor(state);
    expect(stats.Hard).toEqual({ count: 8, bestMs: 1000, averageMs: 16000, bestAverageMs: 4500 });
  });

  it("equals the plain average when there are too few samples to trim (n < 4)", () => {
    let state = createPlayerArchive();
    state = recordSolveTime(state, "Medium", 1000);
    state = recordSolveTime(state, "Medium", 3000);

    const stats = timeStatsFor(state);
    expect(stats.Medium!.bestAverageMs).toBe(stats.Medium!.averageMs);
  });

  it("keeps stats independent per difficulty", () => {
    let state = createPlayerArchive();
    state = recordSolveTime(state, "Easy", 1000);
    state = recordSolveTime(state, "Hard", 5000);

    const stats = timeStatsFor(state);
    expect(stats.Easy!.count).toBe(1);
    expect(stats.Hard!.count).toBe(1);
    expect(stats.Medium).toBeNull();
    expect(stats["Extra Hard"]).toBeNull();
  });
});
