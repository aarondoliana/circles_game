// Client-side port of validator.py's R2/R3 checks, extended with enough
// coordinate detail (which row/col, which triplet) for the UI to draw the
// red outlines the design doc calls for -- the Python side only ever needed
// a pass/fail summary for tests, so it didn't need this detail.
import { SIZE, TARGET_COUNT, Value, type GridValues, type Row } from "./types";

export interface R2Violation {
  kind: "row" | "col";
  index: number;
}

export interface R3Violation {
  kind: "row" | "col";
  index: number;
  start: number; // triplet occupies [start, start+1, start+2] along the line
}

export interface ValidationResult {
  isValid: boolean;
  r2Violations: R2Violation[];
  r3Violations: R3Violation[];
}

function lineViolatesR2(line: readonly Value[]): boolean {
  const full = line.filter((v) => v === Value.Full).length;
  const empty = line.filter((v) => v === Value.Empty).length;
  return full > TARGET_COUNT || empty > TARGET_COUNT;
}

function r3StartsInLine(line: readonly Value[]): number[] {
  const starts: number[] = [];
  for (let i = 0; i <= SIZE - 3; i++) {
    const [a, b, c] = [line[i], line[i + 1], line[i + 2]];
    if (a === Value.Blank || b === Value.Blank || c === Value.Blank) continue;
    if (a === c && a !== b) starts.push(i);
  }
  return starts;
}

function column(grid: GridValues, c: number): Row {
  return grid.map((row) => row[c]) as unknown as Row;
}

export function validate(grid: GridValues): ValidationResult {
  const r2Violations: R2Violation[] = [];
  const r3Violations: R3Violation[] = [];

  for (let r = 0; r < SIZE; r++) {
    const row = grid[r];
    if (lineViolatesR2(row)) r2Violations.push({ kind: "row", index: r });
    for (const start of r3StartsInLine(row)) r3Violations.push({ kind: "row", index: r, start });
  }
  for (let c = 0; c < SIZE; c++) {
    const col = column(grid, c);
    if (lineViolatesR2(col)) r2Violations.push({ kind: "col", index: c });
    for (const start of r3StartsInLine(col)) r3Violations.push({ kind: "col", index: c, start });
  }

  return { isValid: r2Violations.length === 0 && r3Violations.length === 0, r2Violations, r3Violations };
}

/** True if (row, col) sits inside any reported R2 line violation. */
export function cellHasR2Violation(result: ValidationResult, row: number, col: number): boolean {
  return result.r2Violations.some((v) => (v.kind === "row" ? v.index === row : v.index === col));
}

/** True if (row, col) sits inside any reported R3 triplet violation. */
export function cellHasR3Violation(result: ValidationResult, row: number, col: number): boolean {
  return result.r3Violations.some((v) => {
    if (v.kind === "row") return v.index === row && col >= v.start && col < v.start + 3;
    return v.index === col && row >= v.start && row < v.start + 3;
  });
}
