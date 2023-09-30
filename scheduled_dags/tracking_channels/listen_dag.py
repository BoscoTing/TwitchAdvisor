from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import os
import sys
sys.path.insert(0, os.getcwd())

from managers.ircbot_manager import TwitchChatListener


def create_listen_dag(parent_dag_name, child_dag_name, channel):

    listener = TwitchChatListener(channel)
    one_minute_ago = datetime.now().utcnow() - timedelta(minutes=1)
    dag = DAG(
        dag_id=f'{parent_dag_name}.{child_dag_name}',
        schedule="@once", 
        start_date=one_minute_ago,
        concurrency=1,
        max_active_runs=1,
    )

    # Define more tasks here as needed
    listen=PythonOperator(
        task_id="listen_to_chatroom",
        python_callable=listener.listen_to_chatroom
        )
    
    return dag