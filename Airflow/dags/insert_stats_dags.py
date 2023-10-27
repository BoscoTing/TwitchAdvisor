import os
import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.api.client.local_client import Client
sys.path.insert(0, os.getcwd())

from plugins.logging_manager import dev_logger
from plugins.viewers_reaction import ViewersReactionAnalyser
from plugins.tracked_channels import get_tracked_channels

client = Client(api_base_url='http://localhost:8080')

"""
1. Query from trackedChannels.
2. Iterate over the tracked channels.
3. Check if there are tracked channels which have unexecuted insert_stats_task (has insert_logs but not insert_stats record of same 'startedAt').
4. Calculate stats for those channels one by one.
"""

tracked_channels_list = get_tracked_channels()

"""
2. Iterate over the tracked channels.
3. Check if there are tracked channels which have unexecuted insert_stats_task.
"""
def complete_insert_stats_for_every_channels():
    for channel in tracked_channels_list:
        analyser = ViewersReactionAnalyser(channel=channel)
        analyser.insert_historical_stats()
        dev_logger.info(f"insert_historical_stats: {channel}")

with DAG(
    "start_insert_stats_dag",
    schedule=timedelta(hours=6), 
    start_date=datetime(2023, 10, 1, 1, 0),
    concurrency=1,
    max_active_runs=1,
    catchup=False
) as dag:
    start_insert_stats_task = PythonOperator(
        task_id="start_insert_stats_task",
        python_callable=complete_insert_stats_for_every_channels
    )

start_insert_stats_task