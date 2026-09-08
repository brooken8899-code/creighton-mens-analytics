"""
Cleans the raw Wyscout "Team Stats" export into a tidy, one-row-per-match
dataframe for Creighton, with proper column names and derived fields:
result, goals for/against, xG differential, and home/away.

Run this once to produce creighton_matches_2025.csv, then build the
Streamlit app on top of that clean file instead of the raw Excel.
"""

import pandas as pd
import re

def clean_wyscout_export(filepath, season_label):
    df = pd.read_excel(filepath, sheet_name="TeamStats")
    df = df.iloc[2:].reset_index(drop=True)  # drop season-summary rows

    def parse_match(row):
        match, team = row["Match"], row["Team"]
        if pd.isna(match) or pd.isna(team):
            return pd.Series([None, None, None, None])
        score_part = match.split()[-1]
        s1, s2 = map(int, score_part.split(":"))
        teams_part = match.rsplit(score_part, 1)[0].strip()
        team_a, team_b = [t.strip() for t in teams_part.split(" - ")]
        is_home = (team == team_a)
        my_goals, opp_goals = (s1, s2) if is_home else (s2, s1)
        opponent = team_b if is_home else team_a
        result = "Win" if my_goals > opp_goals else ("Loss" if my_goals < opp_goals else "Draw")
        return pd.Series([result, my_goals, opp_goals, "Home" if is_home else "Away", opponent])

    df[["Result", "GoalsFor", "GoalsAgainst", "HomeAway", "Opponent"]] = df.apply(parse_match, axis=1)

    creighton = df[df["Team"] == "Creighton Bluejays"].copy()
    creighton["Season"] = season_label
    creighton["xG_diff"] = creighton["GoalsFor"] - creighton["xG"]

    # Keep the columns most relevant to the three questions we're chasing:
    # 1) finishing gap (xG vs goals)  2) home/away splits  3) PPDA pattern
    keep_cols = [
        "Season", "Date", "Opponent", "HomeAway", "Result",
        "GoalsFor", "GoalsAgainst", "xG", "xG_diff",
        "Possession, %", "PPDA",
    ]
    # 2026 file has fewer columns (no PPDA) — only keep what actually exists
    keep_cols = [c for c in keep_cols if c in creighton.columns]
    return creighton[keep_cols].reset_index(drop=True)


if __name__ == "__main__":
    SEASON_FILES = {
        "2022": "/mnt/user-data/uploads/Team_Stats_Creighton_Bluejays__22_.xlsx",
        "2023": "/mnt/user-data/uploads/Team_Stats_Creighton_Bluejays__23_.xlsx",
        "2024": "/mnt/user-data/uploads/Team_Stats_Creighton_Bluejays__24_.xlsx",
        "2025": "/mnt/user-data/uploads/Copy_of_Team_Stats_Creighton_Bluejays__25_.xlsx",
        "2026": "/mnt/user-data/uploads/Copy_of_Team_Stats_Creighton_Bluejays.xlsx",
    }

    all_seasons = []
    for season, path in SEASON_FILES.items():
        cleaned = clean_wyscout_export(path, season)
        cleaned.to_csv(f"creighton_matches_{season}.csv", index=False)
        print(f"{season}: {len(cleaned)} matches")
        all_seasons.append(cleaned)

    combined = pd.concat(all_seasons, ignore_index=True)
    combined.to_csv("creighton_matches_combined.csv", index=False)
    print()
    print("Combined total matches:", len(combined))
    print(combined.groupby("Season").size())
