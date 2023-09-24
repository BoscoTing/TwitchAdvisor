from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.models import DagModel
import airflow.settings
from datetime import datetime, timedelta
import os
import sys
sys.path.insert(0, os.getcwd())

from managers.twitch_api_manager import TwitchDeveloper

def pause_dag(dag, is_paused):
    """
    A way to programatically unpause a DAG.
    :param dag: DAG object
    :return: dag.is_paused is now False
    """
    session = airflow.settings.Session()
    try:
        qry = session.query(DagModel).filter(DagModel.dag_id == dag)#dag.dag_id)
        d = qry.first()
        d.is_paused = is_paused
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()

class ChannelDetect:
    def __init__(self):
        self.twitch_developer = TwitchDeveloper()

    def detect_channel(self):
        channels = ['sneakylol', 'gosu']
        status_list = []
        for channel in channels:
            living = self.twitch_developer.detect_living_channel(channel)
            if living:
                status_list.append(living)

        if len(status_list) == 0:
            pause_dag("insertmany_chat_logs_dag", is_paused=True) # pause DAGs
            pause_dag("query_stats_dag", is_paused=True)
        else:
            pause_dag("insertmany_chat_logs_dag", is_paused=False) # unpause DAGs
            pause_dag("query_stats_dag", is_paused=False)

one_minute_ago = datetime.now().utcnow() - timedelta(minutes=1)
 
with DAG(
    "detect_channel_dag",
    schedule=timedelta(minutes=5), 
    start_date=one_minute_ago,
    concurrency=1,
    max_active_runs=1
) as dag:
    detector=PythonOperator(task_id="detect_channel",
                            python_callable=ChannelDetect().detect_channel)