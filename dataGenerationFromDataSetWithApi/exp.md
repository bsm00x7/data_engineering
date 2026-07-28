# English Premier League Dataset API

A REST API built with **FastAPI** that exposes English Premier League
match data from the **2000/01** season through the **2024/25** season.

## Features

-   Fast REST API
-   Automatic Swagger documentation (`/docs`)
-   Filter matches by season, date, team, and result
-   Team statistics
-   League statistics
-   Head-to-head lookup
-   Pagination
-   Random match endpoint

------------------------------------------------------------------------

# Project Structure

``` text
project/
│
├── main.py          # FastAPI application
├── epl_final.csv    # Dataset
├── pyproject.toml   # Project dependencies
└── README.md
```

------------------------------------------------------------------------

# Requirements

-   Python 3.10+
-   FastAPI
-   Uvicorn
-   Pandas

Install:

``` bash
uv sync
```

or

``` bash
pip install fastapi uvicorn pandas
```

------------------------------------------------------------------------

# Run the API

Using uv:

``` bash
uv run fastapi dev
```

Or:

``` bash
uvicorn main:app --reload
```

Open:

-   http://127.0.0.1:8000
-   http://127.0.0.1:8000/docs
-   http://127.0.0.1:8000/redoc

------------------------------------------------------------------------

# Dataset

Expected CSV columns:

-   Season
-   MatchDate
-   HomeTeam
-   AwayTeam
-   FullTimeHomeGoals
-   FullTimeAwayGoals
-   FullTimeResult
-   HalfTimeHomeGoals
-   HalfTimeAwayGoals
-   HalfTimeResult
-   HomeShots
-   AwayShots
-   HomeShotsOnTarget
-   AwayShotsOnTarget
-   HomeCorners
-   AwayCorners
-   HomeFouls
-   AwayFouls
-   HomeYellowCards
-   AwayYellowCards
-   HomeRedCards
-   AwayRedCards

------------------------------------------------------------------------

# API Endpoints

## General

  Method   Endpoint        Description
  -------- --------------- ---------------------
  GET      `/`             API welcome message
  GET      `/info`         Dataset information
  GET      `/statistics`   League statistics
  GET      `/random`       Random match

## Matches

  Method   Endpoint
  -------- ----------------------------------
  GET      `/matches`
  GET      `/matches/date/{date}`
  GET      `/matches/season/{season}`
  GET      `/matches/team/{team}`
  GET      `/matches/home/{team}`
  GET      `/matches/away/{team}`
  GET      `/matches/result/{result}`
  GET      `/matches/highest-goals`
  GET      `/matches/page/{page}?limit=20`
  GET      `/matches/between/{start}/{end}`

## Teams

  Method   Endpoint
  -------- -------------------------------
  GET      `/teams`
  GET      `/teams/{team}/stats`
  GET      `/search/team/{name}`
  GET      `/headtohead/{team1}/{team2}`

------------------------------------------------------------------------

# Examples

Get matches on a date:

``` text
GET /matches/date/2000-08-19
```

Get Arsenal matches:

``` text
GET /matches/team/Arsenal
```

Get season:

``` text
GET /matches/season/2023/24
```

Get home wins:

``` text
GET /matches/result/H
```

Result codes:

-   H = Home Win
-   D = Draw
-   A = Away Win

------------------------------------------------------------------------

# Responses

Successful responses return JSON.

Example:

``` json
{
  "count": 10,
  "matches": [
    {
      "Season": "2000/01",
      "HomeTeam": "Chelsea",
      "AwayTeam": "West Ham"
    }
  ]
}
```

Errors use HTTP status codes such as:

-   200 OK
-   400 Bad Request
-   404 Not Found
-   500 Internal Server Error

------------------------------------------------------------------------

# Future Improvements

-   Sorting
-   Advanced filtering
-   Authentication
-   Rate limiting
-   Caching
-   Database support
-   Docker deployment
-   Automated tests
-   CI/CD

------------------------------------------------------------------------

# License

Use and modify this project for learning or your own applications.
