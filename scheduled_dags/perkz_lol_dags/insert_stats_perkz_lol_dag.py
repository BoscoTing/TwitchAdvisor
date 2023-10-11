from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import airflow.settings
from airflow.models import DagModel
from datetime import datetime, timedelta
import os
import sys
sys.path.insert(0, os.getcwd())

from features.viewers_reaction import ViewersReactionAnalyser

channel = "perkz_lol"

analyser = ViewersReactionAnalyser(channel)
one_minute_ago = datetime.now().utcnow() - timedelta(minutes=1)

def pause_dag(dag, is_paused): # not in use
    session = airflow.settings.Session()
    try:
        qry = session.query(DagModel).filter(DagModel.dag_id == dag)
        d = qry.first()
        d.is_paused = is_paused
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()

with DAG(
    f"insert_stats_{channel}_dag",
    schedule="@once",
    start_date=one_minute_ago,
    concurrency=1,
    max_active_runs=1
) as dag:
    insert_stats=PythonOperator(
        task_id=f"insert_stats_{channel}",
        python_callable=analyser.insert_historical_stats,
        )
    # pause=PythonOperator(
    #     task_id=f"pause_insert_stats_{channel}",
    #     python_callable=pause_dag,
    #     op_kwargs={
    #         "dag": f"insert_stats_{channel}",
    #         "is_paused": True
    #         }
    #     )

# when insert_stats done, set the dag is_paused = True to ensure it won't be triggered by detect_channel_dag again.
insert_stats # >> pause