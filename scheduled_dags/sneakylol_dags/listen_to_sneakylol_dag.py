from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import configparser
import os
import sys
sys.path.insert(0, os.getcwd())

from managers.ircbot_manager import TwitchChatListener

listener = TwitchChatListener("sneakylol")

one_minute_ago = datetime.now().utcnow() - timedelta(minutes=1)

with DAG(
    "listen_sneakylol_dag",
    schedule="@once", 
    start_date=one_minute_ago,
    concurrency=1,
    max_active_runs=1
) as dag:
    listen=PythonOperator(task_id="listen_to_chatroom",
                          python_callable=listener.listen_to_chatroom)