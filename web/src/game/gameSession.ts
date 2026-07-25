// The Game object from the design doc: a Move history (Memory) plus the
// meta-moves to navigate it (undo/redo/jump/restart/new game), live- or
// on-completion validation as a toggleable Option, and a non-destructive
// "show solution" reveal. `playingGrid` is always derived from
// `moveHistory` replayed up to `currentMoveIndex`, rather than mutated
// directly -- that's what makes undo/redo/jump-to-move trivial and
// unambiguous.
import { SIZE, Value, type ArchivedPuzzle, type GridValues, type Row } from "./types";

export interface Move {
  row: number;
  col: number;
  previousValue: Value;
  newValue: Value;
}

export interface GameState {
  puzzle: ArchivedPuzzle;
  playingGrid: GridValues;
  moveHistory: Move[];
  currentMoveIndex: number; // -1 means "at the starting grid, no moves applied"
  liveValidation: boolean;
  solutionRevealed: boolean;
}

export type GameAction =
  | { type: "MOVE"; row: number; col: number }
  | { type: "UNDO" }
  | { type: "REDO" }
  | { type: "GO_TO_MOVE"; index: number }
  | { type: "RESTART" }
  | { type: "NEW_GAME"; puzzle: ArchivedPuzzle }
  | { type: "TOGGLE_LIVE_VALIDATION" }
  | { type: "TOGGLE_SOLUTION" };

// blank -> full -> empty -> blank
const NEXT_VALUE: Record<Value, Value> = {
  [Value.Blank]: Value.Full,
  [Value.Full]: Value.Empty,
  [Value.Empty]: Value.Blank,
};

function computePlayingGrid(startingGrid: GridValues, moveHistory: Move[], currentMoveIndex: number): GridValues {
  const grid = startingGrid.map((row) => [...row]) as Value[][];
  for (let i = 0; i <= currentMoveIndex; i++) {
    const move = moveHistory[i];
    grid[move.row][move.col] = move.newValue;
  }
  return grid.map((row) => row as unknown as Row) as unknown as GridValues;
}

export function isGivenCell(puzzle: ArchivedPuzzle, row: number, col: number): boolean {
  return puzzle.startingGrid[row][col] !== Value.Blank;
}

export function isGridComplete(grid: GridValues): boolean {
  return grid.every((row) => row.every((v) => v !== Value.Blank));
}

export function initGameState(puzzle: ArchivedPuzzle, liveValidation = true): GameState {
  return {
    puzzle,
    playingGrid: puzzle.startingGrid,
    moveHistory: [],
    currentMoveIndex: -1,
    liveValidation,
    solutionRevealed: false,
  };
}

export function gameReducer(state: GameState, action: GameAction): GameState {
  switch (action.type) {
    case "MOVE": {
      const { row, col } = action;
      if (row < 0 || row >= SIZE || col < 0 || col >= SIZE) return state;
      if (isGivenCell(state.puzzle, row, col)) return state; // givens are locked
      if (state.solutionRevealed) return state; // no editing while viewing the solution

      const previousValue = state.playingGrid[row][col];
      const newValue = NEXT_VALUE[previousValue];
      const moveHistory = [...state.moveHistory.slice(0, state.currentMoveIndex + 1), { row, col, previousValue, newValue }];
      const currentMoveIndex = moveHistory.length - 1;
      return {
        ...state,
        moveHistory,
        currentMoveIndex,
        playingGrid: computePlayingGrid(state.puzzle.startingGrid, moveHistory, currentMoveIndex),
      };
    }
    case "UNDO": {
      if (state.currentMoveIndex < 0) return state;
      const currentMoveIndex = state.currentMoveIndex - 1;
      return { ...state, currentMoveIndex, playingGrid: computePlayingGrid(state.puzzle.startingGrid, state.moveHistory, currentMoveIndex) };
    }
    case "REDO": {
      if (state.currentMoveIndex >= state.moveHistory.length - 1) return state;
      const currentMoveIndex = state.currentMoveIndex + 1;
      return { ...state, currentMoveIndex, playingGrid: computePlayingGrid(state.puzzle.startingGrid, state.moveHistory, currentMoveIndex) };
    }
    case "GO_TO_MOVE": {
      const currentMoveIndex = Math.max(-1, Math.min(action.index, state.moveHistory.length - 1));
      return { ...state, currentMoveIndex, playingGrid: computePlayingGrid(state.puzzle.startingGrid, state.moveHistory, currentMoveIndex) };
    }
    case "RESTART":
      return { ...state, moveHistory: [], currentMoveIndex: -1, playingGrid: state.puzzle.startingGrid, solutionRevealed: false };
    case "NEW_GAME":
      return initGameState(action.puzzle, state.liveValidation);
    case "TOGGLE_LIVE_VALIDATION":
      return { ...state, liveValidation: !state.liveValidation };
    case "TOGGLE_SOLUTION":
      return { ...state, solutionRevealed: !state.solutionRevealed };
    default:
      return state;
  }
}
