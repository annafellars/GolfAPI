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

def compare_players(player1, player2):
    rounds_df = scoreboard_df.melt(
    id_vars=['Name', 'Total Strokes', 'Tournament Status', 'Course Name'], 
    value_vars=['First Round', 'Second Round', 'Third Round', 'Fourth Round'], 
    var_name='Round', 
    value_name='Score')

    player_data = rounds_df[rounds_df['Name'].isin([player1, player2])]

    player_data['Course Name'].replace({
    'Le Golf National': 'Olympics', 
    'Royal Troon': 'Open Champ', 
    'Pinehurst Resort & Country Club (Course No. 2)': 'US Open', 
    'Augusta National Golf Club': 'Masters', 
    'Valhalla Golf Club': 'PGA Champ'
    }, inplace=True)

    avg_scores = player_data.groupby(['Name', 'Course Name'])['Score'].mean().reset_index()
    avg_scores.rename(columns={'Score': 'Average Score'}, inplace=True)

    return avg_scores


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

with tab2:
    # Player Inputs
    input_player1 = st.text_input("Enter the First Player Name:")
    input_player2 = st.text_input("Enter the Second Player Name to Compare:")

    if input_player1 and input_player2:
        # Filter Data for Each Player
        player_summary1 = scoreboard_df[scoreboard_df["Name"] == input_player1]
        player_summary2 = scoreboard_df[scoreboard_df["Name"] == input_player2]

        if not player_summary1.empty and not player_summary2.empty:
            # Display Metrics
            col1, col2 = st.columns(2)
            col1.metric(label=f"{input_player1} Average Position", 
                        value=round(player_summary1["Position"].mean(), 2))
            col2.metric(label=f"{input_player2} Average Position", 
                        value=round(player_summary2["Position"].mean(), 2))

            # Generate Comparison Data
            graph_data = compare_players(input_player1, input_player2)

            # Plotting the Comparison
            fig2 = px.line(
                graph_data, 
                x='Course Name', 
                y='Average Score', 
                color='Name', 
                title="Player Comparison in 2024",
                category_orders = {'Course Name': ['Masters', 'PGA Champ', 'US Open', 'Open Champ', 'Olympics']},
                markers=True
            )
            st.plotly_chart(fig2)
        else:
            st.warning("One or both players not found in the dataset. Please check the names.")
    else:
        st.info("Enter names for both players to compare.")
