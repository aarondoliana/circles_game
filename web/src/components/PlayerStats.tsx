import type { Difficulty } from "../game/types";
import { formatDuration } from "../lib/formatDuration";
import type { PlayerStats as PlayerStatsData, TimeStats } from "../player/playerArchive";

const DIFFICULTIES: Difficulty[] = ["Easy", "Medium", "Hard", "Extra Hard"];

export interface PlayerStatsProps {
  stats: PlayerStatsData;
  timeStats: TimeStats;
  onReset: () => void;
}

export function PlayerStats({ stats, timeStats, onReset }: PlayerStatsProps) {
  const timedDifficulties = DIFFICULTIES.filter((d) => timeStats[d] !== null);

  return (
    <div className="player-stats">
      <p>
        Solved: {stats.total} (Easy {stats.byDifficulty.Easy}, Medium {stats.byDifficulty.Medium}, Hard{" "}
        {stats.byDifficulty.Hard}, Extra Hard {stats.byDifficulty["Extra Hard"]})
        {stats.total > 0 && (
          <>
            {" "}
            &middot; <button type="button" className="player-stats__reset" onClick={onReset}>
              reset stats
            </button>
          </>
        )}
      </p>
      {timedDifficulties.length > 0 && (
        <table className="player-stats__times">
          <thead>
            <tr>
              <th>Difficulty</th>
              <th>Solves</th>
              <th>Best</th>
              <th>Average</th>
              <th>Best average</th>
            </tr>
          </thead>
          <tbody>
            {timedDifficulties.map((d) => {
              const t = timeStats[d]!;
              return (
                <tr key={d}>
                  <td>{d}</td>
                  <td>{t.count}</td>
                  <td>{formatDuration(t.bestMs)}</td>
                  <td>{formatDuration(t.averageMs)}</td>
                  <td>{formatDuration(t.bestAverageMs)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
