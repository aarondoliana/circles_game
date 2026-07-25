import { Value } from "../game/types";

export interface CellProps {
  value: Value;
  given: boolean;
  incorrect: boolean; // live-validation: playing value differs from the solution
  ruleViolation: boolean; // live-validation: part of an R2/R3 violation
  onClick: () => void;
}

function symbolFor(value: Value): string {
  if (value === Value.Full) return "●";
  if (value === Value.Empty) return "○";
  return "";
}

export function Cell({ value, given, incorrect, ruleViolation, onClick }: CellProps) {
  const classNames = ["cell"];
  if (given) classNames.push("cell--given");
  if (incorrect) classNames.push("cell--incorrect");
  if (ruleViolation) classNames.push("cell--rule-violation");

  return (
    <button type="button" className={classNames.join(" ")} onClick={onClick} disabled={given}>
      {symbolFor(value)}
    </button>
  );
}
