"""Read the NFL and MLB repos and reprint the current slate.

Reads nfl_game_predictor artifacts/nfl_next_games.csv, nfl_game_predictor
artifacts/roster_2026_only.csv, and mlb_game_predictor artifacts/seeds.csv.
Does not train. Does not price a prop. Does not copy a roster row.
"""

from __future__ import annotations

import csv
from pathlib import Path

GROK = Path(__file__).resolve().parents[2]
NFL_NEXT = GROK / "nfl_game_predictor" / "artifacts" / "nfl_next_games.csv"
NFL_ROSTER = GROK / "nfl_game_predictor" / "artifacts" / "roster_2026_only.csv"
MLB_SEEDS = GROK / "mlb_game_predictor" / "artifacts" / "seeds.csv"
CUTOFF = "2026-10-01"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    games = read_rows(NFL_NEXT)
    roster = read_rows(NFL_ROSTER)
    mlb_rows = read_rows(MLB_SEEDS)

    print(f"nfl slate {len(games)} source {NFL_NEXT}")
    for row in games:
        print(
            f"{row['date'].strip()} {row['away'].strip()} at {row['home'].strip()} "
            f"home_win_prob {row['home_win_prob'].strip()} "
            f"spread_line {row['spread_line'].strip()} "
            f"total_line {row['total_line'].strip()} "
            f"lean {row['total_lean'].strip()}"
        )

    print(f"roster {NFL_ROSTER.name} rows {len(roster)} copied 0")

    mlb_dates = [(row.get("date") or "").strip() for row in mlb_rows]
    mlb_dates = [date for date in mlb_dates if date]
    if mlb_rows and mlb_dates and all(date < CUTOFF for date in mlb_dates):
        print("mlb_game_predictor artifacts/seeds.csv has only games before 2026-10-01")
        return

    print(f"mlb slate source {MLB_SEEDS}")
    for row in mlb_rows:
        date = (row.get("date") or "").strip()
        if date and date < CUTOFF:
            continue
        away = (row.get("away") or "").strip()
        home = (row.get("home") or "").strip()
        prob = (row.get("home_win_prob") or "").strip()
        print(f"{date} {away} at {home} home_win_prob {prob}")


if __name__ == "__main__":
    main()
