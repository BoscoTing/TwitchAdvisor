import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px

from datetime import datetime
from time import time, sleep, strftime
from pytz import timezone
import os
import sys
sys.path.insert(0, os.getcwd())

from databases.mongodb import connect_mongo
# from data_sources.crawler import get_viewers_count
# from data_sources.chat_logs import listen_to_chatroom, get_chats, parse_chat_mongo
from dashboard_info.chats_bert import analyze_new_msg

channel = "gosu"
df_active = pd.DataFrame(columns=["messages", "chatters", "calculated_at"]).set_index("calculated_at") 
def execute_query():
    collection = connect_mongo("chat_logs")
    query = {
            "$and": [ 
                {"timestamp": { "$gt": time()-10 }}, 
                {"timestamp": { "$lte": time() }} 
                ] 
        }
    messages_count = collection.count_documents(query)
    chatters_count = len(collection.distinct(query=query, key="username"))   
    # viewers_count = get_viewers_count("el_yuste") 
    values = {
                "messages": messages_count, 
                "chatters": chatters_count,
             }
    return values
    # cursor = collection.find(query)

def draw_radar():  
    df = pd.DataFrame(dict(
    r = analyze_new_msg(),
    theta = ['Negative', 'Neural', 'Positive']
    ))
    print(df)
    fig = px.line_polar(df, r='r', theta='theta', line_close=True)
    fig.update_polars(radialaxis=dict(range=[0, 5]))
    return fig

# listen_to_chatroom(channel)
value = execute_query()
# title = st.header("Total Viewers")
line_chart_title = st.header("Audience Interaction")
# text = st.subheader(f"Total Viewers:{get_viewers_count(channel)}")
line_chart = st.line_chart(df_active, height=10)
radar_chart_title = st.header("Sentiment Analysis")
# radar_chart_text = st.subheader(f"Recent messages: {value['messages']}")
radar_chart = st.plotly_chart(draw_radar())

while True:
    # chat_log = get_chats()
    # parse_chat_mongo(chat_log)
    value = execute_query()
    df_active = df_active._append(
        pd.DataFrame(
            value,
            index=[ datetime.now(timezone("ROC")).strftime('%H:%M:%S') ]
        )
    )
    line_chart.line_chart(df_active, height=400)
    # text.subheader(f"Total Viewers: {get_viewers_count(channel)}")
    # radar_chart_text.subheader(f"Recent messages: {value['messages']}")
    print(value['messages'])
    radar_chart.plotly_chart(draw_radar())
    sleep(1)