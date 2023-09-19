import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from datetime import datetime
from time import time, sleep, strftime
from pytz import timezone
import sys
sys.path.insert(0, "/Users/surfgreen/B/AppworksSchool/projects/personal_project")

from databases.mongodb import connect_mongo
from data_sources.crawler import get_viewers_count

df_active = pd.DataFrame(columns=["messages", "chatters", "calculated_at"]).set_index("calculated_at") 
def execute_query():
    collection = connect_mongo("chats")
    query = {
            "$and": [ 
                {"unix_time_stamp": { "$gt": time()-30 }}, 
                {"unix_time_stamp": { "$lte": time() }} 
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

title = st.header("Total Viewers")
text = st.subheader(get_viewers_count("k4yfour"))
line_chart_title = st.header("Audience Interaction")
line_chart = st.line_chart(df_active, height=10)


while True:
    df_active = df_active._append(
        pd.DataFrame(
            execute_query(),
            index=[ datetime.now(timezone("ROC")).strftime('%H:%M:%S') ]
        )
    )
    # sleep(1)
    line_chart.line_chart(df_active, height=400)
    text.subheader(get_viewers_count("k4yfour"))

