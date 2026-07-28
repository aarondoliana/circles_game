import { useEffect, useState } from "react";
import { formatDuration } from "../lib/formatDuration";

export interface TimerProps {
  startedAt: number;
  /** Show Solution was used this attempt -- per the design doc, the timer
   * goes permanently "n/a" rather than keep counting a disqualified run. */
  isNA: boolean;
  isSolved: boolean;
}

export function Timer({ startedAt, isNA, isSolved }: TimerProps) {
  const [now, setNow] = useState(() => Date.now());

  // The component doesn't remount between puzzles, so resync explicitly
  // whenever a new attempt starts -- otherwise `now` stays stale from the
  // previous puzzle and can even predate the new startedAt.
  useEffect(() => {
    setNow(Date.now());
  }, [startedAt]);

  useEffect(() => {
    if (isNA || isSolved) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [isNA, isSolved, startedAt]);

  return <p className="timer">{isNA ? "n/a" : formatDuration(now - startedAt)}</p>;
}
