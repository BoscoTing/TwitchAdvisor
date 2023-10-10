from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.models import DagModel
from airflow.settings import Session
from datetime import datetime, timedelta
import os
import sys
sys.path.insert(0, os.getcwd())

# from scheduled_dags import listen_to_chatroom_dag, insert_chat_logs_dag, query_stats_dag
from managers.twitch_api_manager import TwitchDeveloper
# from features.viewers_reaction import ViewersReactionAnalyser

def pause_dag(dag, is_paused):
    session = Session()
    try:
        qry = session.query(DagModel).filter(DagModel.dag_id == dag)
        d = qry.first()
        d.is_paused = is_paused
        session.commit()
        print(f"set {dag} is_paused: {is_paused}")
    except:
        session.rollback()
    finally:
        session.close()

def check_is_paused(dag): # not in use
    session = Session()
    try:
        print(f"check if {dag} is paused.")
        dag_model = session.query(DagModel).filter(DagModel.dag_id == dag).first()

    except Exception as e:
        print(f"Error triggering DAGs: {str(e)}")

    finally:
        session.close()

    if dag_model:
        print(f"{dag} is_paused: {dag_model.is_paused}")
        return dag_model.is_paused


def track_live_channels():
    twitch_developer = TwitchDeveloper()
    channels = ['sneakylol', 'gosu', 'scarra', 'disguisedtoast', 'trick2g', 'midbeast', 'perkz_lol']
    for channel in channels:
        dag_list_streaming = [f"listen_{channel}_dag"]
        living = twitch_developer.detect_living_channel(channel) 
        # find the living channels
        if living: 
            print(f"{channel} is living")
            for downstream_dags in dag_list_streaming:
                # start two tracking dags for each channel
                pause_dag(downstream_dags, is_paused=False) 
        else:
            for downstream_dags in dag_list_streaming:
                print(f"{channel} is off-line")
                pause_dag(downstream_dags, is_paused=True)

def detect_live_channels(): 
    twitch_developer = TwitchDeveloper()
    channels = ['sneakylol', 'gosu', 'scarra', 'disguisedtoast', 'trick2g', 'midbeast', 'perkz_lol']
    live_channels = []
    for channel in channels:
        living = twitch_developer.detect_living_channel(channel)
        if living:
            live_channels.append(channel)
    return live_channels

def detect_offline_channels(): 
    twitch_developer = TwitchDeveloper()
    channels = ['sneakylol', 'gosu', 'scarra', 'disguisedtoast', 'trick2g', 'midbeast', 'perkz_lol']
    offline_channels = []
    for channel in channels:
        living = twitch_developer.detect_living_channel(channel)
        if living == False:
            offline_channels.append(channel)
    return offline_channels

def skip():
    print("No dags need to be triggered")

# one_minute_ago = datetime.now().utcnow() - timedelta(minutes=10)

with DAG(
    "detect_channel_dag",
    schedule=timedelta(minutes=15), 
    start_date=datetime(2023, 10, 1, 0, 0),
    concurrency=1,
    max_active_runs=1,
    catchup=False
) as dag:
    start_tracking=PythonOperator(
        task_id="detect_live_channel",
        python_callable=track_live_channels,
    )
    # start_tracking
    live_channels = detect_live_channels()
    offline_channels = detect_offline_channels()
    print(offline_channels)


    """
    Set start_listening, start_stats to do nothing in default.
    Prevent from no tasks were assigned.
    """
    start_listening=PythonOperator(
        task_id="default_skip_listening",
        python_callable=skip,
    ) 

    start_stats=PythonOperator(
        task_id="default_skip_stats",
        python_callable=skip,
    ) 

    """
    if there are live_channels or offline_channels, assign TriggerDagRunOperator to tasks.
    """
    for live_channel in live_channels:
        start_listening=TriggerDagRunOperator(
            task_id=f"trigger_listen_{live_channel}",
            trigger_dag_id=f"listen_{live_channel}_dag",
        )

    for offline_channel in offline_channels:
        start_logs=TriggerDagRunOperator(
            task_id=f"trigger_insert_logs_{offline_channel}",
            trigger_dag_id=f"insert_logs_{offline_channel}_dag",
        )
        start_stats=TriggerDagRunOperator(
            task_id=f"trigger_insert_stats_{offline_channel}",
            trigger_dag_id=f"insert_stats_{offline_channel}_dag",
        )

    # if live_channels == []: # all channels are offline
    #     start_tracking >> start_logs >> start_stats
    # elif offline_channels == []: # all channels are live
    #     start_tracking >> start_listening
    # else:
    
start_tracking >> start_logs >> start_stats >> start_listening