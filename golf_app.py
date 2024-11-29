import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import requests
from io import BytesIO
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Load API key
with open("golf_API_key", "r") as file:
    api_key = file.read().strip()

base_url = "https://live-golf-data.p.rapidapi.com/leaderboard"
headers = {
    "x-rapidapi-key": api_key,
    "x-rapidapi-host": "live-golf-data.p.rapidapi.com",
}

# Function to fetch and process scoreboard data
def scoreboard(year, tourn_id):
    scoreboard_list = []
    params = {"orgId": "1", "tournId": tourn_id, "year": year}
    response = requests.get(base_url, headers=headers, params=params)
    
    if response.status_code != 200:
        st.error(f"Failed to fetch data: {response.status_code}")
        return pd.DataFrame()  # Return empty dataframe on failure
    
    data = response.json()
    for score in data.get("leaderboardRows", []):
        rounds = score.get("rounds", [])
        first_round_score = rounds[0].get("strokes", {}).get("$numberInt") if len(rounds) > 0 else None
        second_round_score = rounds[1].get("strokes", {}).get("$numberInt") if len(rounds) > 1 else None
        third_round_score = rounds[2].get("strokes", {}).get("$numberInt") if len(rounds) > 2 else None
        fourth_round_score = rounds[3].get("strokes", {}).get("$numberInt") if len(rounds) > 3 else None
        course_name = rounds[0].get("courseName") if rounds else None

        score_info = {
            "Name": f"{score.get('firstName')} {score.get('lastName')}",
            "Course Name": course_name,
            "Position": score.get("position"),
            "Strokes Under": score.get("total"),
            "Total Strokes": score.get("totalStrokesFromCompletedRounds"),
            "First Round": first_round_score,
            "Second Round": second_round_score,
            "Third Round": third_round_score,
            "Fourth Round": fourth_round_score,
            "Fourth Round Tee Time": score.get("teeTime"),
            "Amateur Status": score.get("isAmateur"),
            "Tournament Status": score.get("status"),
            "ID": score.get("playerId"),
        }
        scoreboard_list.append(score_info)

    return pd.DataFrame(scoreboard_list)

# Streamlit App
st.title("Charting the Course")

tab1, tab2 = st.tabs(["Years", "Players"])

# Tournament mapping
tournament_ids = {
    "Olympics": 519,
    "Open Champ": 100,
    "Masters": 14,
    "US Open": 26,
    "PGA Champ": 33,
}

with tab1:
    input_year = st.text_input("Enter a Year:")
    input_tournament = st.selectbox("Select a Tournament", list(tournament_ids.keys()))
    tourn_id = tournament_ids[input_tournament]

    if input_year and tourn_id:
        score_data = scoreboard(input_year, tourn_id)
        if not score_data.empty:
            st.dataframe(score_data)
        else:
            st.warning("No data available for the selected year and tournament.")
