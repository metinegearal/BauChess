from config import MONGODB_URI, MONGODB_DATABASE, STOCKFISH_PATH
from config import read_people, PGN_DATA_DIR
from datetime import date, datetime
import numpy as np
from pymongo import MongoClient
import streamlit as st
import pandas as pd
from DataProcess import processGames
from StockFishReview import stockfishDataProcess
import plotly.express as px


with st.sidebar:
    add_radio = st.radio(
        "Choose data width",
        ("per game", "between games")
    )
    user = st.selectbox(
    "User:",
    read_people())

    try:
        gameDate=st.date_input("Game Start Day:",min_value=date(2025,9,1),max_value=date.today())
        text=(PGN_DATA_DIR / f"pgn_data_{gameDate.strftime('%Y-%m-%d')}_{user}.txt").read_text()
    except:
        st.write("No data for this user on that day")
        text=""

    if add_radio=="per game":
        maxValue=len(text.split(" ***Space*** "))-1 
        num=st.number_input("GameNumber:",min_value=0,max_value=max(0,maxValue-1),value=0,step=1)
    else:
        gameDateFinish=st.date_input("Game Finish Day:",min_value=date(gameDate.year,gameDate.month,gameDate.day),max_value=date.today())
        num=0
# st.write(text)


if not user:
    st.info("Add players to people.txt to get started.")
    st.stop()
output=processGames(user,text.split(" ***Space*** ")[num]) if text else {}

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DATABASE]
stats= db["stats"]

if add_radio=="per game":
    if text=="":
        st.stop()
    st.write("Average Time Per Move:", output["AverageTimePerMove"])
    st.write("Game Summary:", output["summary"])
    st.write("Game Accuracy:", output["accuracy"])
    st.write("Opening:", output["opening"])
    st.write("Phase-wise Accuracy:", output["phases"])
    st.write("ColorPlayer:", output["UserColor"])

    if output["TimePerMove"]:
        df = pd.DataFrame({
            "MoveType": output["typeList"][:len(output["TimePerMove"])],
            "TimePerMove": output["TimePerMove"]
        })
        #st.line_chart(df, y="TimePerMove")
        fig = px.line(df, y="TimePerMove", title="Speed and Move Quality")
        fig.add_scatter(
            y=df["TimePerMove"], 
            mode="markers", 
            marker=dict(color=df["MoveType"].map({
                "best": "green",
                "excellent": "lightgreen",
                "good": "lightgreen",
                "inaccuracy": "orange",
                "mistake": "red",
                "blunder": "darkred"
            }))
        )
        st.plotly_chart(fig, use_container_width=True)




    df2 = pd.DataFrame({
        "Color": ["#FFFFFF" if i%2==0 else "#000000" for i in range(len(output["evalList"]))],
        "Eval": output["evalList"]
    })
    fig2 = px.line(df2, y="Eval", title="Eval Trend")
    fig2.add_scatter(
        y=df2["Eval"], 
        mode="markers", 
        marker=dict(color=df2["Color"])
        # marker=dict(color=df["type"].map({
        #     "Best": "green",
        #     "Good": "lightgreen",
        #     "Inaccuracy": "orange",
        #     "Mistake": "red",
        #     "Blunder": "darkred"
        # }))
    )
    st.plotly_chart(fig2, use_container_width=True)

elif add_radio=="between games":
    # dataStats={"GameDate":output["Date"],"PlayerName":user,"TimePerMove":output["AverageTimePerMove"],"TotalTime":output["TimeControl"],"NumMoves":output["summary"]["total_moves"],"Accuracy":output["accuracy"],"Blunders":output["summary"]["blunder"],"Mistakes":output["summary"]["mistake"],"Inaccuracies":output["summary"]["inaccuracy"],"AvgCentipawnLoss":np.mean(output["centipawnLoseList"]),"MaxCentipawnLoss":max(output["centipawnLoseList"]),"PlayElo":"On progress","UserElo":output["WhiteElo"] if output["UserColor"]=="White" else output["BlackElo"],"OpponentElo":output["WhiteElo"] if output["UserColor"]=="Black" else output["BlackElo"],"Opening":output["opening"],"Result":output["Result"],"Termination":output["Termination"]}
    
    dfStats=pd.DataFrame(stats.find({"PlayerName": user,"GameDate": {"$gte": datetime.combine(gameDate, datetime.min.time()), "$lte": datetime.combine(gameDateFinish, datetime.min.time())}}))
    if dfStats.empty:
        st.write("No data for this user")
        st.stop()
    dfStats["win"]=dfStats["Termination"].apply(lambda x: 1 if user in x and "won" in x else 0.5 if "draw" in x else 0)
    st.write(dfStats)
    fig = px.line(dfStats, y="TimePerMove", title="Evarage time spent per move")
    fig.add_scatter(
        y=dfStats["TimePerMove"], 
        mode="markers", 
        marker=dict(color=dfStats["win"].map({1: "green", 0.5: "yellow", 0: "red"}))
    )
    st.plotly_chart(fig, use_container_width=True)
    fig2 = px.line(dfStats, y="Blunders", title="Blunder per game")
    fig2.add_scatter(
        y=dfStats["Blunders"], 
        mode="markers", 
        marker=dict(color=dfStats["win"].map({1: "green", 0.5: "yellow", 0: "red"}))
    )
    st.plotly_chart(fig2, use_container_width=True)
    fig3 = px.line(dfStats, y="AvgCentipawnLoss", title="Average Centipawn Loss")
    fig3.add_scatter(
        y=dfStats["AvgCentipawnLoss"], 
        mode="markers", 
        marker=dict(color=dfStats["win"].map({1: "green", 0.5: "yellow", 0: "red"}))
    )
    st.plotly_chart(fig3, use_container_width=True)
    fig4 = px.line(dfStats, y="Accuracy", title="Accuracy")
    fig4.add_scatter(
        y=dfStats["Accuracy"], 
        mode="markers", 
        marker=dict(color=dfStats["win"].map({1: "green", 0.5: "yellow", 0: "red"}))
    )
    st.plotly_chart(fig4, use_container_width=True)


