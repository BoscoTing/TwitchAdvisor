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
    "insert_logs_trick2g_dag",
    schedule=timedelta(seconds=30), 
    start_date=one_minute_ago,
    concurrency=1,
    max_active_runs=1
) as dag:
    insert=PythonOperator(task_id="insert_logs_trick2g_logs",
                          python_callable=analyser.insert_chat_logs,
                          op_kwargs={"file": os.getcwd()+ f'/dags/chat_logs/{analyser.channel}.log'})