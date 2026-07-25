import { describe, expect, it } from "vitest";
import { Value, type GridValues } from "../types";
import { cellHasR2Violation, cellHasR3Violation, validate } from "../validator";

const F = Value.Full;
const E = Value.Empty;
const B = Value.Blank;

// The design doc's own worked solution.
const SOLVED_EXAMPLE: GridValues = [
  [E, F, F, E, E, E, F, F],
  [F, E, E, F, F, F, E, E],
  [F, E, E, F, F, F, E, E],
  [E, F, F, E, E, E, F, F],
  [E, F, F, E, E, E, F, F],
  [F, E, E, F, F, F, E, E],
  [F, E, E, F, F, F, E, E],
  [E, F, F, E, E, E, F, F],
] as unknown as GridValues;

function cloneGrid(grid: GridValues): number[][] {
  return grid.map((row) => [...row]);
}

describe("validate", () => {
  it("accepts the design doc's worked solution", () => {
    const result = validate(SOLVED_EXAMPLE);
    expect(result.isValid).toBe(true);
  });

  it("flags a row with too many FULL cells (R2)", () => {
    const values = cloneGrid(SOLVED_EXAMPLE);
    values[0] = [F, F, F, F, F, E, E, E];
    const result = validate(values as unknown as GridValues);
    expect(result.isValid).toBe(false);
    expect(result.r2Violations).toContainEqual({ kind: "row", index: 0 });
  });

  it("flags an alternating triplet (R3)", () => {
    const values = cloneGrid(SOLVED_EXAMPLE);
    values[0][0] = F;
    values[0][1] = E;
    values[0][2] = F;
    const result = validate(values as unknown as GridValues);
    expect(result.isValid).toBe(false);
    expect(result.r3Violations).toContainEqual({ kind: "row", index: 0, start: 0 });
  });

  it("allows a run of three of the same kind", () => {
    // SOLVED_EXAMPLE row 0 positions 3,4,5 are already E,E,E.
    const result = validate(SOLVED_EXAMPLE);
    expect(result.r3Violations.find((v) => v.kind === "row" && v.index === 0)).toBeUndefined();
  });

  it("ignores blank cells", () => {
    const blankGrid = Array.from({ length: 8 }, () => Array(8).fill(B)) as unknown as GridValues;
    const result = validate(blankGrid);
    expect(result.isValid).toBe(true);
  });
});

describe("cellHasR2Violation / cellHasR3Violation", () => {
  it("locates R2 violations to every cell in the offending row/col", () => {
    const values = cloneGrid(SOLVED_EXAMPLE);
    values[0] = [F, F, F, F, F, E, E, E];
    const result = validate(values as unknown as GridValues);
    for (let c = 0; c < 8; c++) expect(cellHasR2Violation(result, 0, c)).toBe(true);
    // col 1 is untouched by the row-0 edit (F there matches the original), so
    // it stays balanced -- unlike col 0, which the edit also throws off.
    expect(cellHasR2Violation(result, 1, 1)).toBe(false);
  });

  it("locates R3 violations to exactly the offending triplet", () => {
    const values = cloneGrid(SOLVED_EXAMPLE);
    values[0][0] = F;
    values[0][1] = E;
    values[0][2] = F;
    const result = validate(values as unknown as GridValues);
    expect(cellHasR3Violation(result, 0, 0)).toBe(true);
    expect(cellHasR3Violation(result, 0, 1)).toBe(true);
    expect(cellHasR3Violation(result, 0, 2)).toBe(true);
    // col 7 is far enough from the edit that no triplet touching it changed.
    expect(cellHasR3Violation(result, 0, 7)).toBe(false);
  });
});
