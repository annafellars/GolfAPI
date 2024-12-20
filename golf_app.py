import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import os

# api_key = st.secrets["GOLF_API_KEY"]

# base_url = "https://live-golf-data.p.rapidapi.com/leaderboard"
# headers = {
#     "x-rapidapi-key": api_key,
#     "x-rapidapi-host": "live-golf-data.p.rapidapi.com",
# }

scoreboard_df = pd.read_csv("clean_scoreboard_df.csv")

def avg_scores(data):

    rounds_df = data.melt(
        id_vars=['ID', 'Total Strokes', 'Tournament Status'], 
        value_vars=['First Round', 'Second Round', 'Third Round', 'Fourth Round'], 
        var_name='Round', 
        value_name='Score'
    )

    round_order = ['First Round', 'Second Round', 'Third Round', 'Fourth Round']
    rounds_df['Round'] = pd.Categorical(rounds_df['Round'], categories=round_order, ordered=True)

    valid_players = rounds_df[rounds_df["Tournament Status"] == "complete"]

    avg_scores = valid_players.groupby('Round')['Score'].mean().reset_index()
    avg_scores.rename(columns={'Score': 'Average Score'}, inplace=True)

    winning_player = valid_players.loc[valid_players['Total Strokes'].idxmin()]
    losing_player = valid_players.loc[valid_players['Total Strokes'].idxmax()]

    winning_scores = valid_players[valid_players['ID'] == winning_player['ID']][['Round', 'Score']]
    winning_scores.rename(columns={'Score': 'First Place Score'}, inplace=True)
    losing_scores = valid_players[valid_players['ID'] == losing_player['ID']][['Round', 'Score']]
    losing_scores.rename(columns={'Score': 'Last Place Score'}, inplace = True)
    
    summary = avg_scores.merge(winning_scores, on='Round', how='left')
    summary = summary.merge(losing_scores, on='Round', how='left')

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

    course_order = ['Masters', 'PGA Champ', 'US Open', 'Open Champ', 'Olympics']
    player_data['Course Name'] = pd.Categorical(player_data['Course Name'], categories=course_order, ordered=True)

    avg_scores = player_data.groupby(['Name', 'Course Name'])['Score'].mean().reset_index()
    avg_scores.rename(columns={'Score': 'Average Score'}, inplace=True)

    return avg_scores


# Streamlit App
st.title("Charting the Course")

#layout
with st.sidebar:
    st.write("Other resources!")
    st.link_button("API documentation", "https://slashgolf.dev/docs.html#tag/PGA-Tour-Information")
    st.link_button("More PGA Stats", "https://www.pgatour.com/stats")

    st.write("Have any questions? Contact me on LinkedIn")
    st.link_button("LinkedIn", "https://www.linkedin.com/in/anna-fellars/")

tab1, tab2, tab3 = st.tabs(["Home", "2024 Majors", "Player Stats"])

# Tournament mapping
tournament_ids = {
    "Olympics": "Le Golf National",
    "Open Champ": "Royal Troon",
    "Masters": "Augusta National Golf Club",
    "US Open": "Pinehurst Resort & Country Club (Course No. 2)",
    "PGA Champ": "Valhalla Golf Club"
}

course_to_tournament = {v: k for k, v in tournament_ids.items()}

with tab1:
    st.subheader("Welcome!")
    st.write("This app is dedicated to making golf more fun! Play around with comparing players and viewing Major Tournament Stats. Check out my blog post on how I collected the data, or on a golf analysis.")
    cola, colb = st.columns(2, gap="medium")
    cola.link_button("API Data Collection", "https://annafellars.github.io/annablog/blog/PGA-Analysis/")
    colb.link_button("PGA Data Analysis", "https://annafellars.github.io/annablog/blog/PGA-Prediction/")
    st.video("https://www.youtube.com/watch?v=Ot6rwdU84qs")

with tab2:
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
        custom_colors = {
            'Average Score': '#2274A5', 
            'First Place Score': '#3BC14A', 
            'Last Place Score': '#BF211E'  
        }

        # Create the figure
        fig = px.line(
            summary_data.melt(id_vars='Round', var_name='Metric', value_name='Score'),
            x='Round',
            y='Score',
            color='Metric',
            title='Round Metrics Summary',
            markers=True,
            color_discrete_map=custom_colors
        )

        st.plotly_chart(fig)
    else:
        st.warning("No valid score data available.")

with tab3:
    # Player Inputs
    input_player1 = st.text_input("Enter the First Player Name:", "Scottie Scheffler")
    input_player2 = st.text_input("Enter the Second Player Name to Compare:", "Xander Schauffele")


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
            
            #Position data
            players_data = scoreboard_df[scoreboard_df["Name"].isin([input_player1, input_player2])]
            players_data['Course Name'].replace(course_to_tournament, inplace=True)

            # Create position_df with players as rows and tournaments as columns
            position_df = players_data.pivot(index='Name', columns='Course Name', values='Position')
            position_df.reset_index(inplace=True)  # Reset index for better display

            st.subheader("Player Positions by Tournament")
            st.dataframe(position_df)

            # Generate Comparison Data
            graph_data = compare_players(input_player1, input_player2)

            custom_colors2 = {
                input_player1: '#2274A5', 
                input_player2: '#D1BCE3' 
            }
            # Plotting the Comparison
            fig2 = px.line(
                graph_data, 
                x='Course Name', 
                y='Average Score', 
                color='Name',
                title="Player Comparison in 2024",
                category_orders={'Course Name': ['Masters', 'PGA Champ', 'US Open', 'Open Champ', 'Olympics']},
                markers=True,
                color_discrete_map=custom_colors2
            )
            st.subheader("Average Round by Tournament")
            st.plotly_chart(fig2)
        else:
            st.warning("One or both players not found in the dataset. Please check the names.")
    else:
        st.info("Enter names for both players to compare.")
