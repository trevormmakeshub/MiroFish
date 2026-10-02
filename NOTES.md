MiroFish reads the NFL and MLB repos when scripts/read_repos.py runs.
It does not run on a timer.
roster_2026_only.csv is the prop sheet.
A seed is not a bet.
The recorded line is not a live book price.

scripts/read_repos.py reads nfl_game_predictor artifacts/nfl_next_games.csv, artifacts/seeds.csv, and artifacts/roster_2026_only.csv, and mlb_game_predictor artifacts/seeds.csv. It writes seeds/nfl_current.csv from the games still on the next-game file and seeds/mlb_current.csv from the baseball seed file. A baseball row dated before 2026-10-01 is skipped. Live score is the one ESPN call. It does not train. It does not price a prop. No roster row is copied. Seeds dated before 2026-10-01 are removed.
