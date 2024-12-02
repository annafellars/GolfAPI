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

scoreboard_df = pd.read_csv("clean_scoreboard_df.csv")

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
    valid_players = rounds_df[rounds_df["Tournament Status"] == "complete"]

    # Calculate the average score for each round
    avg_scores = valid_players.groupby('Round')['Score'].mean().reset_index()
    avg_scores.rename(columns={'Score': 'Average Score'}, inplace=True)

    winning_player = valid_players.loc[valid_players['Total Strokes'].idxmin()]
    losing_player = valid_players.loc[valid_players['Total Strokes'].idxmax()]

    winning_scores = valid_players[valid_players['ID'] == winning_player['ID']][['Round', 'Score']]
    losing_scores = valid_players[valid_players['ID'] == losing_player['ID']][['Round', 'Score']]

    # Merge the winning and losing player's scores with the average scores
    summary = avg_scores.merge(winning_scores, on='Round', how='left')
    summary = summary.merge(losing_scores, on='Round', how='left')
    summary.rename(columns={'Score Winning': 'Winning Player Score', 'Score Losing': 'Losing Player Score'}, inplace=True)

    return summary

# Streamlit App
st.title("Charting the Course")

tab1, tab2 = st.tabs(["2024 Majors", "Player Stats"])

# Tournament mapping
tournament_ids = {
    "Olympics": "Le Golf National",
    "Open Champ": "Royal Troon",
    "Masters": "Augusta National Golf Club",
    "US Open": "Pinehurst Resort & Country Club (Course No. 2)",
    "PGA Champ": "Valhalla Golf Club"
}

with tab1:
    input_tournament = st.selectbox("Select a Tournament:", list(tournament_ids.keys()))
    tourn_id = tournament_ids[input_tournament]

    with st.expander("See Dataframe"):
        score_data = scoreboard_df[scoreboard_df["Course Name"] == tourn_id]
        if not score_data.empty:
            st.dataframe(score_data)
        else:
            st.warning("No data available for the selected tournament.")
    
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