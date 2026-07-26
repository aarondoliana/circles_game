import { describe, expect, it } from "vitest";
import type { ArchivedPuzzle } from "../../game/types";
import {
  createPlayerArchive,
  isSolved,
  loadPlayerArchive,
  recordSolved,
  savePlayerArchive,
  statsFor,
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
