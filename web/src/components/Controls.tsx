import type { GameState } from "../game/gameSession";
import type { Difficulty } from "../game/types";

const DIFFICULTIES: Difficulty[] = ["Easy", "Medium", "Hard", "Extra Hard"];

export interface ControlsProps {
  state: GameState;
  onUndo: () => void;
  onRedo: () => void;
  onRestart: () => void;
  onToggleLiveValidation: () => void;
  onToggleSolution: () => void;
  onNewGame: (difficulty: Difficulty) => void;
}

export function Controls({
  state,
  onUndo,
  onRedo,
  onRestart,
  onToggleLiveValidation,
  onToggleSolution,
  onNewGame,
}: ControlsProps) {
  const canUndo = state.currentMoveIndex >= 0;
  const canRedo = state.currentMoveIndex < state.moveHistory.length - 1;

  return (
    <div className="controls">
      <div className="controls__row">
        <button type="button" onClick={onUndo} disabled={!canUndo}>
          Undo
        </button>
        <button type="button" onClick={onRedo} disabled={!canRedo}>
          Redo
        </button>
        <button type="button" onClick={onRestart}>
          Restart
        </button>
        <button type="button" onClick={onToggleSolution}>
          {state.solutionRevealed ? "Hide solution" : "Show solution"}
        </button>
      </div>
      <label className="controls__checkbox">
        <input type="checkbox" checked={state.liveValidation} onChange={onToggleLiveValidation} />
        Live validation
      </label>
      <div className="controls__row">
        <span>New game:</span>
        {DIFFICULTIES.map((difficulty) => (
          <button key={difficulty} type="button" onClick={() => onNewGame(difficulty)}>
            {difficulty}
          </button>
        ))}
      </div>
    </div>
  );
}
