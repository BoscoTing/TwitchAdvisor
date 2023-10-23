from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.models import DagRun
from airflow.api.client.local_client import Client
client = Client(api_base_url='http://localhost:8080')
from datetime import datetime, timedelta
import os
import sys
sys.path.insert(0, os.getcwd())

from plugins.logging_manager import dev_logger
from plugins.twitch_api_manager import TwitchDeveloper
from plugins.mongodb_manager import MongoDBManager

"""
1. Query from trackedChannels.
2. Check if channels we are tracking are online.
3. Trigger insert_logs_dags for offline channels.
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
dev_logger.info(f"current_tracking_channels: {tracked_channels_list}")


with DAG(
    "start_insert_logs_dag",
    schedule=timedelta(hours=3), 
    start_date=datetime(2023, 10, 1, 0, 0),
    concurrency=1,
    max_active_runs=1,
    catchup=False
) as dag:

    twitch_developer = TwitchDeveloper()
    for channel in tracked_channels_list:
        living = twitch_developer.detect_living_channel(channel) 
        """
        3. Trigger insert_logs_dags for offline channels.
        """
        if living:
            dev_logger.debug(f"{channel} is online.")

        else:
            dev_logger.debug(f"{channel} is offline.")

            dag_id = f'{channel}_insert_logs_dags'
            dag_runs = DagRun.find(dag_id=dag_id, state='running')

            if dag_runs:
                dev_logger.debug(f"DAG '{dag_id}' is currently running.")

            else:
                dev_logger.debug(f"DAG '{dag_id}' is not running, trigger {dag_id}")
                trigger_insert_logs_task=TriggerDagRunOperator(
                    task_id=f"trigger_{channel}_insert_logs_task",
                    trigger_dag_id=f"{channel}_insert_logs_dag",
                )