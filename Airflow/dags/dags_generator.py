import os
import sys
from datetime import datetime
from airflow.decorators import dag, task
sys.path.insert(0, os.getcwd())

from plugins.twitch_api_manager import TwitchDeveloper
from plugins.ircbot_manager import TwitchChatListener
from plugins.viewers_reaction import ViewersReactionAnalyser
from plugins.tracked_channels import get_tracked_channels


"""
1. From mongodb query the tracking channels.
2. Create DAGs using Airflow REST API.
3. Send request to Twitch API for checking if the channel is on-line.
4. Trigger DAGs in repective condition.
"""


"""
1. From mongodb query the tracking channels.
"""
tracked_channels_list = get_tracked_channels()

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

    dynamic_generated_listen_dag()
    dynamic_generated_insert_logs_dag()

"""
3. Send request to Twitch API for checking if the channel is online.
"""
twitch_developer = TwitchDeveloper()
live_channels_list = []
for tracked_channel in tracked_channels_list:
    is_live = twitch_developer.detect_living_channel(channel=tracked_channel)

    if is_live:
        live_channels_list.append(tracked_channel)