from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.models import DagModel
import airflow.settings
from datetime import datetime, timedelta
import logging
import os
import sys
sys.path.insert(0, os.getcwd())

# from scheduled_dags import listen_to_chatroom_dag, insert_chat_logs_dag, query_stats_dag
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
        self.channels = ['sneakylol', 'gosu', 'scarra', 'disguisedtoast', 'trick2g', 'midbeast', 'perkz_lol']
        
    def dags_beggining(self, channel):
        dag_list_streaming = [f"insert_logs_{channel}_dag", f"listen_{channel}_dag"]
        return dag_list_streaming

    def dags_end(self, channel):
        dag_list_historical = [f"insert_stats_{channel}_dag"]
        return dag_list_historical

    def detect_channel(self):
        for channel in self.channels:
            living = self.twitch_developer.detect_living_channel(channel)
            dag_begging = self.dags_beggining(channel)
            dag_end = self.dags_end(channel)
            if living:
                for dag in dag_end:
                    pause_dag(dag, is_paused=True)

                for dag in dag_begging:
                    pause_dag(dag, is_paused=False)

            else:
                for dag in dag_begging:
                    pause_dag(dag, is_paused=True)

                for dag in dag_end:
                    pause_dag(dag, is_paused=False)


one_minute_ago = datetime.now().utcnow() - timedelta(minutes=1)
 
with DAG(
    "detect_channel_dag",
    schedule=timedelta(minutes=5), 
    start_date=one_minute_ago,
    concurrency=1,
    max_active_runs=1
) as dag:
    detect=PythonOperator(task_id="detect_channel",
                            python_callable=ChannelDetect().detect_channel)