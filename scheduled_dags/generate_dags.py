import os
import sys
sys.path.insert(0, os.getcwd())
from datetime import datetime
from airflow import DAG
from airflow.decorators import dag, task
from airflow.operators.python_operator import PythonOperator
from airflow.models import DagModel
from airflow.settings import Session

from managers.logging_manager import dev_logger, send_log
from managers.twitch_api_manager import TwitchDeveloper
from managers.mongodb_manager import MongoDBManager
from managers.ircbot_manager import TwitchChatListener
from features.viewers_reaction import ViewersReactionAnalyser


"""
1. From mongodb query the tracking channels.
2. Create DAGs using Airflow REST API.
3. Send request to Twitch API for checking if the channel is on-line.
4. Trigger DAGs in repective condition.
"""


"""
1. From mongodb query the tracking channels.
"""
db = MongoDBManager()
tracked_channels_collection = db.connect_collection("trackedChannels") # query from "trackingChannels" collection
query = [
        {
            "$sort":{"addedTime": -1}
            }, 
        {
            "$limit": 1
            }
    ] # the query to get the tracked channels 
result = tracked_channels_collection.aggregate(query)
tracked_channels_list = [row['channels'] for row in result][0]
dev_logger.info("current_tracking_channels: ", tracked_channels_list)
# tracked_channels_list = ['sneakylol', 'gosu', 'scarra', 'disguisedtoast', 'trick2g', 'midbeast', 'perkz_lol']


"""
2. Create DAGs for it using Airflow REST API.
"""    
for tracked_channel in tracked_channels_list:

    @dag(dag_id=f"{tracked_channel}_listen_dag", start_date=datetime(2023, 10, 1), schedule="@once", catchup=False, max_active_runs=1)
    def dynamic_generated_listen_dag():
        channel = tracked_channel # prevent from using wrong 'tracked_channel' for 'listen_to_channel_task' due to for loop
        @task
        def listen_to_channel_task():
            listener = TwitchChatListener(channel)
            listener.listen_to_chatroom()
        listen_to_channel_task()

    @dag(dag_id=f"{tracked_channel}_insert_logs_dag", start_date=datetime(2023, 10, 1), schedule="@once", catchup=False, max_active_runs=1)
    def dynamic_generated_insert_logs_dag():
        channel = tracked_channel # prevent from using wrong 'tracked_channel' for 'listen_to_channel_task' due to for loop
        @task
        def insert_logs_task():
            analyser = ViewersReactionAnalyser(channel)
            analyser.insert_chat_logs()
        insert_logs_task()

    @dag(dag_id=f"{tracked_channel}_insert_stats_dag", start_date=datetime(2023, 10, 1), schedule="@once", catchup=False,  max_active_runs=1)
    def dynamic_generated_insert_stats_dag():
        channel = tracked_channel # prevent from using wrong 'tracked_channel' for 'listen_to_channel_task' due to for loop
        @task
        def insert_stats_task():
            analyser = ViewersReactionAnalyser(channel)
            analyser.insert_historical_stats()
        insert_stats_task()



    dynamic_generated_listen_dag()
    dynamic_generated_insert_logs_dag()
    dynamic_generated_insert_stats_dag()



"""
3. Send request to Twitch API for checking if the channel is online.
"""
twitch_developer = TwitchDeveloper()
live_channels_list = []
for tracked_channel in tracked_channels_list:
    is_live = twitch_developer.detect_living_channel(channel=tracked_channel)

    if is_live:
        live_channels_list.append(tracked_channel)