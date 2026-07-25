// Mirrors constants.py. A plain const object (not `enum`) because the
// project's tsconfig sets erasableSyntaxOnly, which disallows `enum`.
export const Value = {
  Blank: -1,
  Empty: 0,
  Full: 1,
} as const;
export type Value = (typeof Value)[keyof typeof Value];

export const SIZE = 8;
export const TARGET_COUNT = SIZE / 2;

export type Row = readonly [Value, Value, Value, Value, Value, Value, Value, Value];
export type GridValues = readonly [Row, Row, Row, Row, Row, Row, Row, Row];

export type Difficulty = "Easy" | "Medium" | "Hard" | "Extra Hard";

export interface ArchivedPuzzle {
  id: string;
  startingGrid: GridValues;
  solutionGrid: GridValues;
  givenCells: number;
  difficulty: Difficulty;
}
