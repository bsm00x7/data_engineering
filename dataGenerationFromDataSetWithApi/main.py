from fastapi import FastAPI, HTTPException
import pandas as pd
import random

app = FastAPI(
    title="English Premier League API",
    description="Premier League dataset API (2000/01 - 2024/25)",
    version="1.0.0"
)

# ==========================
# Load Dataset
# ==========================
df = pd.read_csv("epl_final.csv")
df["MatchDate"] = pd.to_datetime(df["MatchDate"])

# ==========================
# Root
# ==========================

@app.get("/")
def root():
    return {
        "message": "English Premier League API",
        "matches": len(df),
        "seasons": df["Season"].nunique()
    }

# ==========================
# Info
# ==========================

@app.get("/info")
def info():
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "seasons": sorted(df["Season"].unique().tolist())
    }

# ==========================
# All Matches
# ==========================

@app.get("/matches")
def all_matches():
    return df.to_dict(orient="records")

# ==========================
# Match by Date
# ==========================

@app.get("/matches/date/{date}")
def match_by_date(date: str):
    temp = df[df["MatchDate"] == pd.to_datetime(date)]

    return {
        "count": len(temp),
        "matches": temp.to_dict(orient="records")
    }

# ==========================
# Season
# ==========================

@app.get("/matches/season/{season}")
def season(season: str):
    temp = df[df["Season"] == season]

    return {
        "count": len(temp),
        "matches": temp.to_dict(orient="records")
    }

# ==========================
# Team
# ==========================

@app.get("/matches/team/{team}")
def team(team: str):
    temp = df[
        (df["HomeTeam"].str.lower() == team.lower()) |
        (df["AwayTeam"].str.lower() == team.lower())
    ]

    return {
        "count": len(temp),
        "matches": temp.to_dict(orient="records")
    }

# ==========================
# Home Matches
# ==========================

@app.get("/matches/home/{team}")
def home_matches(team: str):
    temp = df[df["HomeTeam"].str.lower() == team.lower()]

    return {
        "count": len(temp),
        "matches": temp.to_dict(orient="records")
    }

# ==========================
# Away Matches
# ==========================

@app.get("/matches/away/{team}")
def away_matches(team: str):
    temp = df[df["AwayTeam"].str.lower() == team.lower()]

    return {
        "count": len(temp),
        "matches": temp.to_dict(orient="records")
    }

# ==========================
# Teams
# ==========================

@app.get("/teams")
def teams():
    teams = sorted(
        set(df["HomeTeam"]).union(df["AwayTeam"])
    )

    return teams

# ==========================
# Match Result
# ==========================

@app.get("/matches/result/{result}")
def result(result: str):
    temp = df[df["FullTimeResult"] == result.upper()]

    return {
        "count": len(temp),
        "matches": temp.to_dict(orient="records")
    }

# ==========================
# Head To Head
# ==========================

@app.get("/headtohead/{team1}/{team2}")
def head_to_head(team1: str, team2: str):
    temp = df[
        (
            (df["HomeTeam"].str.lower() == team1.lower()) &
            (df["AwayTeam"].str.lower() == team2.lower())
        ) |
        (
            (df["HomeTeam"].str.lower() == team2.lower()) &
            (df["AwayTeam"].str.lower() == team1.lower())
        )
    ]

    return {
        "count": len(temp),
        "matches": temp.to_dict(orient="records")
    }

# ==========================
# Random Match
# ==========================

@app.get("/random")
def random_match():
    row = df.sample(1)
    return row.to_dict(orient="records")[0]

# ==========================
# Statistics
# ==========================

@app.get("/statistics")
def statistics():

    total_matches = len(df)

    home_wins = len(df[df["FullTimeResult"] == "H"])
    away_wins = len(df[df["FullTimeResult"] == "A"])
    draws = len(df[df["FullTimeResult"] == "D"])

    total_goals = (
        df["FullTimeHomeGoals"].sum() +
        df["FullTimeAwayGoals"].sum()
    )

    avg_goals = total_goals / total_matches

    return {
        "matches": total_matches,
        "home_wins": home_wins,
        "away_wins": away_wins,
        "draws": draws,
        "total_goals": int(total_goals),
        "average_goals": round(avg_goals, 2)
    }

# ==========================
# Team Statistics
# ==========================

@app.get("/teams/{team}/stats")
def team_stats(team: str):

    home = df[df["HomeTeam"].str.lower() == team.lower()]
    away = df[df["AwayTeam"].str.lower() == team.lower()]

    if len(home) == 0 and len(away) == 0:
        raise HTTPException(404, "Team not found")

    played = len(home) + len(away)

    wins = len(home[home["FullTimeResult"] == "H"]) + \
           len(away[away["FullTimeResult"] == "A"])

    draws = len(home[home["FullTimeResult"] == "D"]) + \
            len(away[away["FullTimeResult"] == "D"])

    losses = played - wins - draws

    goals_for = \
        home["FullTimeHomeGoals"].sum() + \
        away["FullTimeAwayGoals"].sum()

    goals_against = \
        home["FullTimeAwayGoals"].sum() + \
        away["FullTimeHomeGoals"].sum()

    return {
        "team": team,
        "played": played,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": int(goals_for),
        "goals_against": int(goals_against)
    }

# ==========================
# Highest Scoring Matches
# ==========================

@app.get("/matches/highest-goals")
def highest_goals():

    temp = df.copy()

    temp["Goals"] = (
        temp["FullTimeHomeGoals"] +
        temp["FullTimeAwayGoals"]
    )

    temp = temp.sort_values("Goals", ascending=False)

    return temp.head(20).to_dict(orient="records")

# ==========================
# Search Team
# ==========================

@app.get("/search/team/{name}")
def search(name: str):

    teams = sorted(
        set(df["HomeTeam"]).union(df["AwayTeam"])
    )

    return [
        team
        for team in teams
        if name.lower() in team.lower()
    ]

# ==========================
# Latest Match
# ==========================

@app.get("/latest")
def latest():

    temp = df.sort_values("MatchDate", ascending=False)

    return temp.iloc[0].to_dict()

# ==========================
# First Match
# ==========================

@app.get("/first")
def first():

    temp = df.sort_values("MatchDate")

    return temp.iloc[0].to_dict()

# ==========================
# Pagination
# ==========================

@app.get("/matches/page/{page}")
def pagination(page: int = 1, limit: int = 20):

    start = (page - 1) * limit
    end = start + limit

    return {
        "page": page,
        "limit": limit,
        "matches": df.iloc[start:end].to_dict(orient="records")
    }

# ==========================
# Matches Between Dates
# ==========================

@app.get("/matches/between/{start}/{end}")
def between(start: str, end: str):

    start = pd.to_datetime(start)
    end = pd.to_datetime(end)

    temp = df[
        (df["MatchDate"] >= start) &
        (df["MatchDate"] <= end)
    ]

    return {
        "count": len(temp),
        "matches": temp.to_dict(orient="records")
    }