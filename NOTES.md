MiroFish reads the NFL and MLB repos at run time.
Live score is the one ESPN call.
roster_2026_only.csv is the prop sheet.
A seed is not a bet.
The recorded line is not a live book price.

seeds/nfl_current.csv is one row per game still on nfl_game_predictor artifacts/nfl_next_games.csv. Those cells are copied from that file. scripts/read_repos.py reads that next-game file, roster_2026_only.csv, and mlb_game_predictor artifacts/seeds.csv, then reprints the slate. It does not train. It does not price a prop. No roster row is copied. Seeds dated before 2026-10-01 are removed.
