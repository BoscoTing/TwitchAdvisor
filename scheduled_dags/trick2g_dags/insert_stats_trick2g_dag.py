from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import os
import sys
sys.path.insert(0, os.getcwd())

from features.viewers_reaction import ViewersReactionAnalyser

analyser = ViewersReactionAnalyser("trick2g")
one_minute_ago = datetime.now().utcnow() - timedelta(minutes=1)
with DAG(
    "insert_stats_trick2g_dag",
    schedule="@once",
    start_date=one_minute_ago,
    concurrency=1,
    max_active_runs=1
) as dag:
    insert=PythonOperator(
        task_id="insert_stats_trick2g",
        python_callable=analyser.insert_historical_stats,
        )