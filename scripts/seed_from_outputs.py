"""Write one MiroFish seed per row in a sports repo's prediction CSV.

Reads prediction files the sports repos already wrote. Skips a repo that
wrote none. Does not copy model code and does not pull league stats.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

GROK = Path(r"C:\Users\trevo\grok-mlb")
REPOS = (
    "baseball-predictions",
    "mlb-predictions",
    "mlb-runline",
    "NBA-Machine-Learning-Sports-Betting",
    "sports-betting",
    "model-aggregator",
)
SEEDS = Path(__file__).resolve().parents[1] / "seeds"
LINE = "these numbers are from that repo's model and are not a bet."


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-") or "game"


def prediction_csvs(repo: Path) -> list[Path]:
    found = []
    if not repo.is_dir():
        return found
    for path in repo.rglob("*.csv"):
        parts = {part.lower() for part in path.parts}
        name = path.name.lower()
        if "odds" in parts or "archive" in parts:
            continue
        if "completed" in name or name.startswith("schedule"):
            continue
        if name == "latest.csv" and "predictions" in parts:
            found.append(path)
        elif "prediction" in name and "validation" not in name:
            found.append(path)
    return sorted(found)


def teams(row: dict[str, str]) -> tuple[str, str]:
    away = row.get("awayteamfull") or row.get("away") or row.get("Away Team") or ""
    home = row.get("hometeamfull") or row.get("home") or row.get("Home Team") or ""
    return away.strip(), home.strip()


def main() -> None:
    SEEDS.mkdir(parents=True, exist_ok=True)
    written = 0
    for repo_name in REPOS:
        paths = prediction_csvs(GROK / repo_name)
        if not paths:
            print(f"skip {repo_name}")
            continue
        for path in paths:
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            if not rows:
                print(f"skip empty {path}")
                continue
            for index, row in enumerate(rows, start=1):
                away, home = teams(row)
                date = (row.get("date") or row.get("Date") or "").strip()
                if not date or not away or not home:
                    continue
                body = [f"source: {repo_name}", f"date: {date}", f"away: {away}", f"home: {home}"]
                for key, value in row.items():
                    if key is None or key.lower() in {"date", "awayteamfull", "hometeamfull", "away", "home"}:
                        continue
                    body.append(f"{key}: {value.strip()}")
                body.append(LINE)
                name = f"{slug(repo_name)}-{date}-{slug(away)}-at-{slug(home)}-{index}.txt"
                (SEEDS / name).write_text("\n".join(body) + "\n", encoding="utf-8")
                written += 1
            print(f"{repo_name} {path.name} rows {len(rows)}")
    print(f"seeds {written}")


if __name__ == "__main__":
    main()
