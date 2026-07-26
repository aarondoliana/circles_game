import type { PlayerStats as PlayerStatsData } from "../player/playerArchive";

export interface PlayerStatsProps {
  stats: PlayerStatsData;
  onReset: () => void;
}

export function PlayerStats({ stats, onReset }: PlayerStatsProps) {
  return (
    <p className="player-stats">
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
  );
}
