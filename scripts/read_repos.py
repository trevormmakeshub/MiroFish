"""Read the NFL and MLB repos and write the current seed files.

On each run this reads the sibling repos. It does not paste a saved copy.
It does not train. It does not price a prop. It does not copy a roster row.
It does not run on a timer. The only live request is one NFL scoreboard call.
"""

from __future__ import annotations

import csv
import json
import urllib.error
import urllib.request
from pathlib import Path

GROK = Path(__file__).resolve().parents[2]
MIRO = Path(__file__).resolve().parents[1]
NFL_NEXT = GROK / "nfl_game_predictor" / "artifacts" / "nfl_next_games.csv"
NFL_SEEDS = GROK / "nfl_game_predictor" / "artifacts" / "seeds.csv"
NFL_ROSTER = GROK / "nfl_game_predictor" / "artifacts" / "roster_2026_only.csv"
MLB_SEEDS = GROK / "mlb_game_predictor" / "artifacts" / "seeds.csv"
SEEDS = MIRO / "seeds"
NFL_OUT = SEEDS / "nfl_current.csv"
MLB_OUT = SEEDS / "mlb_current.csv"
ESPN_OUT = MIRO / "data" / "live" / "espn_scoreboard.json"
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
CUTOFF = "2026-10-01"
COLUMNS = [
    "date",
    "away",
    "home",
    "home_win_prob",
    "spread_line",
    "total_line",
    "lean",
    "live_score",
    "source",
]
NFL_SOURCE = "trevormmakeshub/nfl_game_predictor artifacts/nfl_next_games.csv"
MLB_SOURCE = "trevormmakeshub/mlb_game_predictor artifacts/seeds.csv"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def cell(row: dict[str, str], key: str) -> str:
    return (row.get(key) or "").strip()


def fetch_scoreboard() -> tuple[str, dict | None]:
    """One scoreboard request. A non-200 status is recorded and the run continues."""
    ESPN_OUT.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        ESPN_URL,
        headers={"Accept": "application/json", "User-Agent": "mirofish-read/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status = str(getattr(response, "status", 200))
            body = response.read()
    except urllib.error.HTTPError as exc:
        status = str(exc.code)
        body = exc.read()
        ESPN_OUT.write_bytes(body)
        print(f"espn_status {status}")
        return status, None
    except Exception as exc:
        status = f"{type(exc).__name__} {exc}"
        print(f"espn_status {status}")
        return status, None
    ESPN_OUT.write_bytes(body)
    print(f"espn_status {status}")
    if status != "200":
        return status, None
    return status, json.loads(body.decode("utf-8"))


def scoreboard_events(payload: dict | None) -> list[dict[str, str]]:
    events = []
    if not payload:
        return events
    for event in payload.get("events") or []:
        competitions = event.get("competitions") or []
        if not competitions:
            continue
        sides: dict[str, tuple[str, str]] = {}
        for side in competitions[0].get("competitors") or []:
            team = side.get("team") or {}
            score = side.get("score")
            sides[side.get("homeAway") or ""] = (
                str(team.get("abbreviation") or ""),
                "" if score is None else str(score),
            )
        if "away" in sides and "home" in sides:
            events.append(
                {
                    "away_abbr": sides["away"][0],
                    "away_score": sides["away"][1],
                    "home_abbr": sides["home"][0],
                    "home_score": sides["home"][1],
                }
            )
    return events


def live_score(events: list[dict[str, str]], away: str, home: str) -> str:
    exact = [
        event
        for event in events
        if event["away_abbr"] == away and event["home_abbr"] == home
    ]
    away_hits = [event for event in events if event["away_abbr"] == away]
    home_hits = [event for event in events if event["home_abbr"] == home]
    chosen = None
    if len(exact) == 1:
        chosen = exact[0]
    elif len(away_hits) == 1 and not home_hits:
        chosen = away_hits[0]
    elif len(home_hits) == 1 and not away_hits:
        chosen = home_hits[0]
    if chosen is None:
        return ""
    return (
        f"{chosen['away_abbr']} {chosen['away_score']}, "
        f"{chosen['home_abbr']} {chosen['home_score']}"
    )


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def file_dates(path: Path) -> list[str]:
    dates = []
    name = path.name
    if len(name) >= 10 and name[4] == "-" and name[7] == "-":
        prefix = name[:10]
        if prefix[0:4].isdigit() and prefix[5:7].isdigit() and prefix[8:10].isdigit():
            dates.append(prefix)
    if path.suffix.lower() == ".csv":
        for row in read_rows(path):
            date = cell(row, "date")
            if date:
                dates.append(date)
        return dates
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("date:"):
            date = line.split(":", 1)[1].strip()
            if date:
                dates.append(date)
    return dates


def delete_old_seeds() -> list[str]:
    deleted = []
    for path in sorted(SEEDS.iterdir()):
        if not path.is_file():
            continue
        dates = file_dates(path)
        if dates and all(date < CUTOFF for date in dates):
            path.unlink()
            deleted.append(path.name)
    return deleted


def main() -> None:
    next_games = read_rows(NFL_NEXT)
    nfl_seed_rows = read_rows(NFL_SEEDS)
    roster = read_rows(NFL_ROSTER)
    mlb_rows = read_rows(MLB_SEEDS)
    roster_rows_copied = 0

    status, payload = fetch_scoreboard()
    events = scoreboard_events(payload)

    nfl_out = []
    for row in next_games:
        away = cell(row, "away")
        home = cell(row, "home")
        nfl_out.append(
            {
                "date": cell(row, "date"),
                "away": away,
                "home": home,
                "home_win_prob": cell(row, "home_win_prob"),
                "spread_line": cell(row, "spread_line"),
                "total_line": cell(row, "total_line"),
                "lean": cell(row, "total_lean"),
                "live_score": live_score(events, away, home),
                "source": NFL_SOURCE,
            }
        )
    write_rows(NFL_OUT, nfl_out)

    mlb_out = []
    skipped = 0
    for row in mlb_rows:
        date = cell(row, "date")
        if date and date < CUTOFF:
            skipped += 1
            continue
        away = cell(row, "away")
        home = cell(row, "home")
        mlb_out.append(
            {
                "date": date,
                "away": away,
                "home": home,
                "home_win_prob": cell(row, "home_win_prob"),
                "spread_line": cell(row, "spread_line"),
                "total_line": cell(row, "total_line"),
                "lean": cell(row, "lean"),
                "live_score": live_score(events, away, home),
                "source": MLB_SOURCE,
            }
        )
    write_rows(MLB_OUT, mlb_out)
    deleted = delete_old_seeds()

    dates = [row["date"] for row in nfl_out + mlb_out if row["date"]]
    nfl_seed_dates = [cell(row, "date") for row in nfl_seed_rows if cell(row, "date")]
    print(f"nfl_seeds_read {len(nfl_seed_rows)} file {NFL_SEEDS.name}")
    if nfl_seed_dates:
        print(f"nfl_seeds_max_date {max(nfl_seed_dates)}")
    print(f"roster {NFL_ROSTER.name} rows {len(roster)} copied {roster_rows_copied}")
    print(f"mlb_skipped_before_{CUTOFF} {skipped}")
    print(f"deleted {deleted}")
    print(f"nfl_seed_count {len(nfl_out)}")
    print(f"mlb_seed_count {len(mlb_out)}")
    print(f"max_date {max(dates) if dates else ''}")
    for row in nfl_out:
        if row["away"] == "PIT" and row["home"] == "CLE":
            print("steelers " + ",".join(row[column] for column in COLUMNS))


if __name__ == "__main__":
    main()
