from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import os
# os.environ['SENTENCE_TRANSFORMERS_HOME'] = './.cache'
import sys
sys.path.insert(0, os.getcwd())

from features.chatroom_sentiment import ChatroomSentiment

bert = ChatroomSentiment()
one_minute_ago = datetime.now().utcnow() - timedelta(minutes=1)
with DAG(
    "analyse_sentiment_dag",
    # execution_timeout=timedelta(minutes=10),
    schedule=timedelta(seconds=60), 
    start_date=one_minute_ago,
    concurrency=1,
    max_active_runs=1
) as dag:
    viewer=PythonOperator(task_id="analyse_sentiment",
                          python_callable=bert.analyse_new_messages,
                          schedule=timedelta(seconds=30))
