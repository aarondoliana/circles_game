import { useEffect, useMemo, useReducer, useState } from "react";
import "./App.css";
import { Controls } from "./components/Controls";
import { GridView } from "./components/GridView";
import { PlayerStats } from "./components/PlayerStats";
import { gameReducer, initGameState, isGridComplete, type GameAction, type GameState } from "./game/gameSession";
import type { ArchivedPuzzle, Difficulty } from "./game/types";
import { validate } from "./game/validator";
import {
  createPlayerArchive,
  loadPlayerArchive,
  recordSolved,
  savePlayerArchive,
  statsFor,
  unsolvedPuzzles,
  type PlayerArchiveState,
} from "./player/playerArchive";

function pickPuzzle(
  puzzles: ArchivedPuzzle[],
  playerArchive: PlayerArchiveState,
  difficulty?: Difficulty,
): ArchivedPuzzle | undefined {
  const pool = difficulty ? puzzles.filter((p) => p.difficulty === difficulty) : puzzles;
  if (pool.length === 0) return undefined;
  const preferred = unsolvedPuzzles(playerArchive, pool);
  return preferred[Math.floor(Math.random() * preferred.length)];
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
  const [playerArchive, setPlayerArchive] = useState<PlayerArchiveState>(() => loadPlayerArchive());

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
      const puzzle = pickPuzzle(puzzles, playerArchive);
      if (puzzle) dispatch({ type: "NEW_GAME", puzzle });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [puzzles]);

  useEffect(() => savePlayerArchive(playerArchive), [playerArchive]);

  const isSolved = useMemo(() => {
    if (!state) return false;
    return isGridComplete(state.playingGrid) && validate(state.playingGrid).isValid;
  }, [state]);

  useEffect(() => {
    if (state && isSolved) {
      setPlayerArchive((prev) => recordSolved(prev, state.puzzle.id, state.puzzle.difficulty));
    }
  }, [isSolved, state]);

  if (loadError) return <p className="status status--error">Couldn't load the puzzle archive: {loadError}</p>;
  if (!puzzles || !state) return <p className="status">Loading puzzles...</p>;

  const handleNewGame = (difficulty: Difficulty) => {
    const puzzle = pickPuzzle(puzzles, playerArchive, difficulty) ?? pickPuzzle(puzzles, playerArchive);
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
      <PlayerStats stats={statsFor(playerArchive)} onReset={() => setPlayerArchive(createPlayerArchive())} />
    </div>
  );
}

export default App;
