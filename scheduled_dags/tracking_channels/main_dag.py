from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.subdag_operator import SubDagOperator
from datetime import datetime, timedelta

# Import the sub-DAG creation function
from managers.twitch_api_manager import TwitchDeveloper
from scheduled_dags.tracking_channels.listen_dag import create_listen_dag

class ChannelDetect:
    def __init__(self):
        self.twitch_developer = TwitchDeveloper()
        self.channels = ['sneakylol', 'gosu', 'scarra', 'disguisedtoast']
        
    def detect_channel(self):
        status_list = []
        for channel in self.channels:
            living = self.twitch_developer.detect_living_channel(channel)
            if living:
                status_list.append(channel)

        for living_channel in status_list:
            listen = SubDagOperator(
                task_id='run_subdag',
                subdag=create_listen_dag('main_dag', f'listen_{living_channel}_dag'),
                dag=main_dag,
            )

            listen

one_minute_ago = datetime.now().utcnow() - timedelta(minutes=1)
main_dag = DAG(
    dag_id='main_dag',
    schedule=timedelta(minutes=5), 
    start_date=one_minute_ago,
    concurrency=1,
    max_active_runs=1
)
# Define other tasks in the main DAG
detect = PythonOperator(
    task_id="detect_channel",
    python_callable=ChannelDetect().detect_channel
    )

detect