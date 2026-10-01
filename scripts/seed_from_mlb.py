"""Write one MiroFish seed per row in the 2026 remaining-games file.

This script does not pull league stats and does not price props.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

SOURCE = Path(
    r"C:\Users\trevo\grok-mlb\mlb_game_predictor\artifacts\mlb_2026-09-30_remaining_games.csv"
)
SEEDS = Path(__file__).resolve().parents[1] / "seeds"
LINE = "these numbers are from the 2026 box-score model and are not a bet."


def slug(text: str) -> str:
    lowered = text.strip().lower()
    return re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")


def main() -> None:
    SEEDS.mkdir(parents=True, exist_ok=True)
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    written = []
    for row in rows:
        date = row["date"].strip()
        away = row["away"].strip()
        home = row["home"].strip()
        name = f"{date}-{slug(away)}-at-{slug(home)}.txt"
        body = "\n".join(
            [
                f"date: {date}",
                f"away: {away}",
                f"home: {home}",
                f"starter_away: {row['starter_away'].strip()}",
                f"starter_home: {row['starter_home'].strip()}",
                f"home_win_prob: {row['home_win_prob'].strip()}",
                f"predicted_away_runs: {row['predicted_away_runs'].strip()}",
                f"predicted_home_runs: {row['predicted_home_runs'].strip()}",
                LINE,
                "",
            ]
        )
        path = SEEDS / name
        path.write_text(body, encoding="utf-8")
        written.append(path.name)
    print(f"seeds {len(written)}")
    for name in written:
        print(name)


if __name__ == "__main__":
    main()
