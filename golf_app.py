import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import os

api_key = st.secrets["GOLF_API_KEY"]

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

def avg_scores(data):
    # Reshape the data to long format for easier manipulation
    rounds_df = data.melt(
        id_vars=['ID', 'Total Strokes', 'Tournament Status'], 
        value_vars=['First Round', 'Second Round', 'Third Round', 'Fourth Round'], 
        var_name='Round', 
        value_name='Score'
    )

    # Ensure correct order of rounds
    round_order = ['First Round', 'Second Round', 'Third Round', 'Fourth Round']
    rounds_df['Round'] = pd.Categorical(rounds_df['Round'], categories=round_order, ordered=True)

    # Filter for players with 'complete' tournament status
    valid_players = rounds_df[rounds_df['Tournament Status'] == 'complete']

    # Calculate the average score for each round
    avg_scores = valid_players.groupby('Round')['Score'].mean().reset_index()
    avg_scores.rename(columns={'Score': 'Average Score'}, inplace=True)

    # Find the winning player (player with the lowest total strokes)
    winning_player = data.loc[data['Total Strokes'].idxmin()]
    
    # Get the winning player's scores across rounds
    winning_player_scores = rounds_df[rounds_df['ID'] == winning_player['ID']]

    # Find the losing player (player with the highest total strokes)
    losing_player = data.loc[data['Total Strokes'].idxmax()]

    # Get the losing player's scores across rounds
    losing_player_scores = rounds_df[rounds_df['ID'] == losing_player['ID']]

    # Merge the winning and losing player's scores with the average scores
    summary = avg_scores.merge(winning_player_scores[['Round', 'Score']], on='Round', how='left')
    summary = summary.rename(columns={'Score': 'Winning Player Score'})
    
    summary = summary.merge(losing_player_scores[['Round', 'Score']], on='Round', how='left')
    summary = summary.rename(columns={'Score': 'Losing Player Score'})

    return summary

# Streamlit App
st.title("Charting the Course")

tab1, tab2 = st.tabs(["Years", "Players"])

# Tournament mapping
tournament_ids = {
    "Olympics": "519",
    "Open Champ": "100",
    "Masters": "014",
    "US Open": "026",
    "PGA Champ": "033"
}

with tab1:
    input_year = st.selectbox("Select a Year:", ("2021", "2022", "2023", "2024"))
    input_tournament = st.selectbox("Select a Tournament:", list(tournament_ids.keys()))
    tourn_id = tournament_ids[input_tournament]

    with st.expander("See Dataframe"):
        if input_year and tourn_id:
            score_data = scoreboard(input_year, tourn_id)
            if not score_data.empty:
                st.dataframe(score_data)
            else:
                st.warning("No data available for the selected year and tournament.")
    
    if not score_data.empty:
        summary_data = avg_scores(score_data)

        # Plotting the summary data
        fig = px.line(
            summary_data.melt(id_vars='Round', var_name='Metric', value_name='Score'),
            x='Round',
            y='Score',
            color='Metric',
            title='Round Metrics Summary'
        )

        st.plotly_chart(fig)
    else:
        st.warning("No valid score data available.")