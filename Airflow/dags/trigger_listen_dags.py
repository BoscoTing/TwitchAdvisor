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
3. Trigger listen_dags for online channels.
4. Terminate listen_dags for offline channels.
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
dev_logger.debug(f"current_tracking_channels: {tracked_channels_list}")

def stop_dag_run(dag_id): # doesn't work
    dag_run = DagRun.find(dag_id=dag_id, state='running')
    """
    dag_run[0] will get the format like:
        <DagRun gosu_listen_dag @ 2023-10-01 00:00:00+00:00: scheduled__2023-10-01T00:00:00+00:00, state:running, queued_at: 2023-10-12 03:28:42.738369+00:00. externally triggered: False>
    Use dag_run[0].run_id to get "scheduled__2023-10-01T00:00:00+00:00", which is the unique dag_run_id.
    """


    if dag_run:
        dev_logger.debug(f"DAG '{dag_id}' is currently running.")

        dag_run_id = dag_run[0].run_id # prepare dag_id and dag_run_id
        dev_logger.debug(f"DAG run ID for DAG '{dag_id}' is {dag_run_id}.")

        try:
            dag_run[0].set_state('failed') # set dag run state to 'success'
            dev_logger.info(f"Successfully Stopped DAG run {dag_run_id} for DAG {dag_id}.")
            
        except Exception as e:
            dev_logger.error(e)

    else:
        dev_logger.debug(f"No running DAG runs found for DAG '{dag_id}'.")


with DAG(
    "start_listen_dag",
    schedule=timedelta(minutes=15), 
    start_date=datetime(2023, 10, 1, 0, 0),
    concurrency=1,
    max_active_runs=1,
    catchup=False
) as dag:

    twitch_developer = TwitchDeveloper()
    for channel in tracked_channels_list:
        living = twitch_developer.detect_living_channel(channel) 

        dag_id = f'{channel}_listen_dag'

        if living:
            """
            3. Trigger listen_dags for online channels.
            """

            dev_logger.debug(f"{channel} is online.")

            dag_run = DagRun.find(dag_id=dag_id, state='running')
            dev_logger.debug("dag_runs: ", dag_run)

            if dag_run:
                dev_logger.debug(f"DAG '{dag_id}' is currently running.")

            else:
                dev_logger.debug(f"DAG '{dag_id}' is not running, trigger {dag_id}")
                start_listen_task=TriggerDagRunOperator(
                    task_id=f"trigger_{channel}_listen_task",
                    trigger_dag_id=f"{channel}_listen_dag",
                )