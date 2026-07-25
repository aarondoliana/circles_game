import type { GameState } from "../game/gameSession";
import { isGivenCell } from "../game/gameSession";
import { Value } from "../game/types";
import { cellHasR2Violation, cellHasR3Violation, validate, type ValidationResult } from "../game/validator";
import { Cell } from "./Cell";

export interface GridViewProps {
  state: GameState;
  onMove: (row: number, col: number) => void;
}

export function GridView({ state, onMove }: GridViewProps) {
  const { puzzle, playingGrid, solutionRevealed } = state;
  const displayGrid = solutionRevealed ? puzzle.solutionGrid : playingGrid;
  const isComplete = playingGrid.every((row) => row.every((v) => v !== Value.Blank));
  const showValidation = !solutionRevealed && (state.liveValidation || isComplete);
  const validation: ValidationResult | null = showValidation ? validate(playingGrid) : null;

  return (
    <div className="grid" role="grid" aria-label="Circles puzzle grid">
      {displayGrid.map((row, r) =>
        row.map((value, c) => {
          const given = isGivenCell(puzzle, r, c);
          const incorrect =
            !solutionRevealed &&
            showValidation &&
            !given &&
            value !== Value.Blank &&
            value !== puzzle.solutionGrid[r][c];
          const ruleViolation =
            !solutionRevealed &&
            validation !== null &&
            (cellHasR2Violation(validation, r, c) || cellHasR3Violation(validation, r, c));
          return (
            <Cell
              key={`${r}-${c}`}
              value={value}
              given={given || solutionRevealed}
              incorrect={incorrect}
              ruleViolation={ruleViolation}
              onClick={() => onMove(r, c)}
            />
          );
        }),
      )}
    </div>
  );
}
