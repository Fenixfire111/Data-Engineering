from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
from airflow.models import Variable, TaskInstance
from pymongo import MongoClient


def read_process_data(ti: TaskInstance) -> bool:
    """read csv file and process of received data"""
    df = pd.read_csv(Variable.get('review_path'))
    df.dropna(how='all', inplace=True)
    df.fillna('-', inplace=True)
    df.sort_values(by=['at'], inplace=True)
    df['content'].replace(r'[^\w\s.,?!]', '', regex=True, inplace=True)
    ti.xcom_push("process_data", df.to_dict('records'))
    return True


def load_data(ti: TaskInstance) -> bool:
    """load the processed data to the database"""
    data = ti.xcom_pull(task_ids="read_process_data", key="process_data")
    client = MongoClient("localhost", 27017)
    db = client["airflow_task"]
    db.collection.insert_many(data)
    client.close()
    return True


with DAG(
        dag_id='reviews_processing',
        start_date=datetime(year=2022, month=7, day=28),
        schedule_interval='@daily',
        catchup=False
) as dag:

    read_process_data = PythonOperator(
        task_id='read_process_data',
        python_callable=read_process_data
    )
    
    load_data = PythonOperator(
        task_id='load_data',
        python_callable=load_data
    )

    read_process_data >> load_data
