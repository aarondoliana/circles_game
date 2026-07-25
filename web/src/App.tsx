import { useEffect, useMemo, useReducer, useState } from "react";
import "./App.css";
import { Controls } from "./components/Controls";
import { GridView } from "./components/GridView";
import { gameReducer, initGameState, isGridComplete, type GameAction, type GameState } from "./game/gameSession";
import type { ArchivedPuzzle, Difficulty } from "./game/types";
import { validate } from "./game/validator";

function pickPuzzle(puzzles: ArchivedPuzzle[], difficulty?: Difficulty): ArchivedPuzzle | undefined {
  const pool = difficulty ? puzzles.filter((p) => p.difficulty === difficulty) : puzzles;
  if (pool.length === 0) return undefined;
  return pool[Math.floor(Math.random() * pool.length)];
}

// Wraps gameReducer so useReducer can start from "no puzzle loaded yet"
// without needing gameReducer itself to handle a null state.
function appReducer(state: GameState | null, action: GameAction): GameState | null {
  if (state === null) return action.type === "NEW_GAME" ? initGameState(action.puzzle) : null;
  return gameReducer(state, action);
}

function App() {
  const [puzzles, setPuzzles] = useState<ArchivedPuzzle[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [state, dispatch] = useReducer(appReducer, null);

  useEffect(() => {
    fetch("/archive.json")
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      })
      .then((data: { puzzles: ArchivedPuzzle[] }) => setPuzzles(data.puzzles))
      .catch((err) => setLoadError(String(err)));
  }, []);

  useEffect(() => {
    if (puzzles && !state) {
      const puzzle = pickPuzzle(puzzles);
      if (puzzle) dispatch({ type: "NEW_GAME", puzzle });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [puzzles]);

  const isSolved = useMemo(() => {
    if (!state) return false;
    return isGridComplete(state.playingGrid) && validate(state.playingGrid).isValid;
  }, [state]);

  if (loadError) return <p className="status status--error">Couldn't load the puzzle archive: {loadError}</p>;
  if (!puzzles || !state) return <p className="status">Loading puzzles...</p>;

  const handleNewGame = (difficulty: Difficulty) => {
    const puzzle = pickPuzzle(puzzles, difficulty) ?? pickPuzzle(puzzles);
    if (puzzle) dispatch({ type: "NEW_GAME", puzzle });
  };

  return (
    <div className="app">
      <h1>Circles</h1>
      <p className="status">
        {state.puzzle.difficulty} &middot; {state.puzzle.givenCells} given cells
        {isSolved && <span className="status--solved"> &middot; Solved!</span>}
      </p>
      <GridView state={state} onMove={(row, col) => dispatch({ type: "MOVE", row, col })} />
      <Controls
        state={state}
        onUndo={() => dispatch({ type: "UNDO" })}
        onRedo={() => dispatch({ type: "REDO" })}
        onRestart={() => dispatch({ type: "RESTART" })}
        onToggleLiveValidation={() => dispatch({ type: "TOGGLE_LIVE_VALIDATION" })}
        onToggleSolution={() => dispatch({ type: "TOGGLE_SOLUTION" })}
        onNewGame={handleNewGame}
      />
    </div>
  );
}

export default App;
