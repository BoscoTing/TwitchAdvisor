from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import os
import sys
sys.path.insert(0, os.getcwd())

from features.viewers_reaction import ViewersReactionAnalyser
channel = "trick2g"
analyser = ViewersReactionAnalyser(channel)
one_minute_ago = datetime.now().utcnow() - timedelta(minutes=1)
with DAG(
    f"insert_logs_{channel}_dag",
    schedule="@once", 
    start_date=one_minute_ago,
    concurrency=1,
    max_active_runs=1
) as dag:
    insert=PythonOperator(task_id=f"insert_logs_{channel}_logs",
                          python_callable=analyser.insert_chat_logs,
                          op_kwargs={"file": os.getcwd()+ f'/dags/chat_logs/{channel}.log'})