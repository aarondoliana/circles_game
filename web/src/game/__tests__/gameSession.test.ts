import { describe, expect, it } from "vitest";
import { gameReducer, initGameState, isGivenCell, isGridComplete } from "../gameSession";
import { Value, type ArchivedPuzzle, type GridValues } from "../types";

const F = Value.Full;
const E = Value.Empty;
const B = Value.Blank;

const SOLUTION: GridValues = [
  [E, F, F, E, E, E, F, F],
  [F, E, E, F, F, F, E, E],
  [F, E, E, F, F, F, E, E],
  [E, F, F, E, E, E, F, F],
  [E, F, F, E, E, E, F, F],
  [F, E, E, F, F, F, E, E],
  [F, E, E, F, F, F, E, E],
  [E, F, F, E, E, E, F, F],
] as unknown as GridValues;

// Row 0 keeps its givens; everything else starts blank, so tests can freely
// move cells without needing to track a large given-cell set.
const STARTING: GridValues = [
  [E, F, F, E, E, E, F, F],
  [B, B, B, B, B, B, B, B],
  [B, B, B, B, B, B, B, B],
  [B, B, B, B, B, B, B, B],
  [B, B, B, B, B, B, B, B],
  [B, B, B, B, B, B, B, B],
  [B, B, B, B, B, B, B, B],
  [B, B, B, B, B, B, B, B],
] as unknown as GridValues;

const PUZZLE: ArchivedPuzzle = {
  id: "test-puzzle",
  startingGrid: STARTING,
  solutionGrid: SOLUTION,
  givenCells: 8,
  difficulty: "Easy",
};

describe("initGameState", () => {
  it("starts with the starting grid, empty history, and no solution shown", () => {
    const state = initGameState(PUZZLE);
    expect(state.playingGrid).toBe(PUZZLE.startingGrid);
    expect(state.moveHistory).toEqual([]);
    expect(state.currentMoveIndex).toBe(-1);
    expect(state.solutionRevealed).toBe(false);
    expect(state.liveValidation).toBe(false);
    expect(state.solutionEverRevealed).toBe(false);
    expect(typeof state.startedAt).toBe("number");
  });
});

describe("MOVE", () => {
  it("cycles a blank-starting cell blank -> full -> empty -> blank", () => {
    let state = initGameState(PUZZLE);
    state = gameReducer(state, { type: "MOVE", row: 1, col: 0 });
    expect(state.playingGrid[1][0]).toBe(F);
    state = gameReducer(state, { type: "MOVE", row: 1, col: 0 });
    expect(state.playingGrid[1][0]).toBe(E);
    state = gameReducer(state, { type: "MOVE", row: 1, col: 0 });
    expect(state.playingGrid[1][0]).toBe(B);
  });

  it("is a no-op on a given cell", () => {
    const state = initGameState(PUZZLE);
    const next = gameReducer(state, { type: "MOVE", row: 0, col: 0 });
    expect(next).toBe(state);
  });

  it("is a no-op while the solution is revealed", () => {
    let state = initGameState(PUZZLE);
    state = gameReducer(state, { type: "TOGGLE_SOLUTION" });
    const next = gameReducer(state, { type: "MOVE", row: 1, col: 0 });
    expect(next).toBe(state);
  });

  it("records each move in history", () => {
    let state = initGameState(PUZZLE);
    state = gameReducer(state, { type: "MOVE", row: 1, col: 0 });
    state = gameReducer(state, { type: "MOVE", row: 1, col: 1 });
    expect(state.moveHistory).toEqual([
      { row: 1, col: 0, previousValue: B, newValue: F },
      { row: 1, col: 1, previousValue: B, newValue: F },
    ]);
    expect(state.currentMoveIndex).toBe(1);
  });

  it("truncates redo-able future moves when a new move is made after undo", () => {
    let state = initGameState(PUZZLE);
    state = gameReducer(state, { type: "MOVE", row: 1, col: 0 }); // move A
    state = gameReducer(state, { type: "UNDO" });
    state = gameReducer(state, { type: "MOVE", row: 1, col: 1 }); // move B, replaces A's redo slot
    expect(state.moveHistory).toHaveLength(1);
    expect(state.moveHistory[0]).toEqual({ row: 1, col: 1, previousValue: B, newValue: F });
    expect(state.playingGrid[1][0]).toBe(B);
    expect(state.playingGrid[1][1]).toBe(F);
  });
});

describe("UNDO / REDO", () => {
  it("moves the pointer back and forth without losing history", () => {
    let state = initGameState(PUZZLE);
    state = gameReducer(state, { type: "MOVE", row: 1, col: 0 });
    state = gameReducer(state, { type: "MOVE", row: 1, col: 0 }); // now empty

    state = gameReducer(state, { type: "UNDO" });
    expect(state.playingGrid[1][0]).toBe(F);
    expect(state.currentMoveIndex).toBe(0);

    state = gameReducer(state, { type: "UNDO" });
    expect(state.playingGrid[1][0]).toBe(B);
    expect(state.currentMoveIndex).toBe(-1);

    // undo past the start is a no-op
    const atStart = state;
    state = gameReducer(state, { type: "UNDO" });
    expect(state).toBe(atStart);

    state = gameReducer(state, { type: "REDO" });
    expect(state.playingGrid[1][0]).toBe(F);
    state = gameReducer(state, { type: "REDO" });
    expect(state.playingGrid[1][0]).toBe(E);

    // redo past the end is a no-op
    const atEnd = state;
    state = gameReducer(state, { type: "REDO" });
    expect(state).toBe(atEnd);
  });
});

describe("GO_TO_MOVE", () => {
  it("jumps directly to an arbitrary point in history, clamped to bounds", () => {
    let state = initGameState(PUZZLE);
    state = gameReducer(state, { type: "MOVE", row: 1, col: 0 });
    state = gameReducer(state, { type: "MOVE", row: 1, col: 1 });
    state = gameReducer(state, { type: "MOVE", row: 1, col: 2 });

    state = gameReducer(state, { type: "GO_TO_MOVE", index: -1 });
    expect(isGridComplete(state.playingGrid)).toBe(false);
    expect(state.playingGrid[1][0]).toBe(B);

    state = gameReducer(state, { type: "GO_TO_MOVE", index: 1 });
    expect(state.playingGrid[1][0]).toBe(F);
    expect(state.playingGrid[1][1]).toBe(F);
    expect(state.playingGrid[1][2]).toBe(B);

    state = gameReducer(state, { type: "GO_TO_MOVE", index: 999 });
    expect(state.currentMoveIndex).toBe(2);
  });
});

describe("RESTART", () => {
  it("clears history and hides the solution, but keeps the timer running and the solution-revealed taint", () => {
    let state = initGameState(PUZZLE);
    const startedAt = state.startedAt;
    state = gameReducer(state, { type: "MOVE", row: 1, col: 0 });
    state = gameReducer(state, { type: "TOGGLE_SOLUTION" });
    state = gameReducer(state, { type: "RESTART" });

    expect(state.moveHistory).toEqual([]);
    expect(state.currentMoveIndex).toBe(-1);
    expect(state.solutionRevealed).toBe(false);
    expect(state.solutionEverRevealed).toBe(true);
    expect(state.startedAt).toBe(startedAt);
    expect(state.playingGrid).toBe(PUZZLE.startingGrid);
  });
});

describe("NEW_GAME", () => {
  it("resets to the new puzzle but keeps the liveValidation preference", () => {
    let state = initGameState(PUZZLE, false);
    state = gameReducer(state, { type: "MOVE", row: 1, col: 0 });

    const otherPuzzle: ArchivedPuzzle = { ...PUZZLE, id: "other" };
    state = gameReducer(state, { type: "NEW_GAME", puzzle: otherPuzzle });

    expect(state.puzzle).toBe(otherPuzzle);
    expect(state.moveHistory).toEqual([]);
    expect(state.liveValidation).toBe(false);
  });

  it("starts a fresh timer and clears the solution-revealed taint", () => {
    let state = initGameState(PUZZLE);
    state = gameReducer(state, { type: "TOGGLE_SOLUTION" });
    const oldStartedAt = state.startedAt;

    const otherPuzzle: ArchivedPuzzle = { ...PUZZLE, id: "other" };
    state = gameReducer(state, { type: "NEW_GAME", puzzle: otherPuzzle });

    expect(state.solutionEverRevealed).toBe(false);
    expect(state.solutionRevealed).toBe(false);
    expect(state.startedAt).toBeGreaterThanOrEqual(oldStartedAt);
  });
});

describe("TOGGLE_LIVE_VALIDATION / TOGGLE_SOLUTION", () => {
  it("flip their respective booleans", () => {
    let state = initGameState(PUZZLE);
    state = gameReducer(state, { type: "TOGGLE_LIVE_VALIDATION" });
    expect(state.liveValidation).toBe(true);

    state = gameReducer(state, { type: "TOGGLE_SOLUTION" });
    expect(state.solutionRevealed).toBe(true);
    state = gameReducer(state, { type: "TOGGLE_SOLUTION" });
    expect(state.solutionRevealed).toBe(false);
  });

  it("keeps solutionEverRevealed sticky even after hiding the solution again", () => {
    let state = initGameState(PUZZLE);
    state = gameReducer(state, { type: "TOGGLE_SOLUTION" });
    expect(state.solutionEverRevealed).toBe(true);
    state = gameReducer(state, { type: "TOGGLE_SOLUTION" });
    expect(state.solutionRevealed).toBe(false);
    expect(state.solutionEverRevealed).toBe(true);
  });
});

describe("isGivenCell / isGridComplete", () => {
  it("identifies given cells from the starting grid", () => {
    expect(isGivenCell(PUZZLE, 0, 0)).toBe(true);
    expect(isGivenCell(PUZZLE, 1, 0)).toBe(false);
  });

  it("detects completeness", () => {
    expect(isGridComplete(STARTING)).toBe(false);
    expect(isGridComplete(SOLUTION)).toBe(true);
  });
});
