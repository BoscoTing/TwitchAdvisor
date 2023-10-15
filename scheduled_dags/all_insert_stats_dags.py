from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.api.client.local_client import Client
client = Client(api_base_url='http://localhost:8080')
from datetime import datetime, timedelta
import os
import sys
sys.path.insert(0, os.getcwd())

from features.viewers_reaction import ViewersReactionAnalyser
from managers.mongodb_manager import MongoDBManager

"""
1. Query from trackedChannels.
2. Iterate over the tracked channels.
3. Check if there are tracked channels which have unexecuted insert_stats_task (has insert_logs but not insert_stats record of same 'startedAt').
4. Calculate stats for those channels one by one.
"""


db = MongoDBManager()
tracked_channels_collection = db.connect_collection("trackedChannels") # query from "trackingChannels" collection
query = [
        {
            "$sort": {"addedTime": -1}
            }, 
        {
            "$limit": 1
            }
    ] # the query to get the tracked channels 
result = tracked_channels_collection.aggregate(query)
tracked_channels_list = [row['channels'] for row in result][0]
print("current_tracking_channels: ", tracked_channels_list)


"""
2. Iterate over the tracked channels.
3. Check if there are tracked channels which have unexecuted insert_stats_task.
"""
def complete_insert_stats_for_every_channels():
    for channel in tracked_channels_list:
        analyser = ViewersReactionAnalyser(channel=channel)
        analyser.insert_historical_stats()

with DAG(
    "start_insert_stats_dag",
    schedule=timedelta(hours=12), 
    start_date=datetime(2023, 10, 2, 1, 0),
    concurrency=1,
    max_active_runs=1,
    catchup=False
) as dag:
    start_insert_stats_task = PythonOperator(
        task_id="start_insert_stats_task",
        python_callable=complete_insert_stats_for_every_channels
    )

start_insert_stats_task