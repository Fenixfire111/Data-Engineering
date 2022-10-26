from datetime import datetime, timedelta
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models.taskinstance import TaskInstance
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from dotenv import load_dotenv
import os

load_dotenv()

# snowflake user
USER = os.getenv('USER')
# snowflake password
PASSWORD = os.getenv('PASSWORD')
# snowflake account
ACCOUNT = os.getenv('ACCOUNT')
# snowflake warehouse
WAREHOUSE = os.getenv('WAREHOUSE')
# snowflake database
DATABASE = os.getenv('DATABASE')
# snowflake schema
SCHEMA = os.getenv('SCHEMA')
# path to csv file
CSV_FILE = os.getenv('csv_file_path')


connection = snowflake.connector.connect(
    user=USER,
    password=PASSWORD,
    account=ACCOUNT,
    warehouse=WAREHOUSE,
    database=DATABASE,
    schema=SCHEMA
)

cursor = connection.cursor()

table_schema = """
    "_ID" VARCHAR(16777216),
    "IOS_APP_ID" NUMBER(38,0),
    "TITLE" VARCHAR(16777216),
    "DEVELOPER_NAME" VARCHAR(16777216),
    "DEVELOPER_IOS_ID" FLOAT,
    "IOS_STORE_URL" VARCHAR(16777216),
    "SELLER_OFFICIAL_WEBSITE" VARCHAR(16777216),
    "AGE_RATING" VARCHAR(16777216),
    "TOTAL_AVERAGE_RATING" FLOAT,
    "TOTAL_NUMBER_OF_RATINGS" FLOAT,
    "AVERAGE_RATING_FOR_VERSION" FLOAT,
    "NUMBER_OF_RATINGS_FOR_VERSION" NUMBER(38,0),
    "ORIGINAL_RELEASE_DATE" VARCHAR(16777216),
    "CURRENT_VERSION_RELEASE_DATE" VARCHAR(16777216),
    "PRICE_USD" FLOAT,
    "PRIMARY_GENRE" VARCHAR(16777216),
    "ALL_GENRES" VARCHAR(16777216),
    "LANGUAGES" VARCHAR(16777216),
    "DESCRIPTION" VARCHAR(16777216)"""

column_names = """
    "_ID",
    "IOS_APP_ID",
    "TITLE",
    "DEVELOPER_NAME",
    "DEVELOPER_IOS_ID",
    "IOS_STORE_URL",
    "SELLER_OFFICIAL_WEBSITE",
    "AGE_RATING",
    "TOTAL_AVERAGE_RATING",
    "TOTAL_NUMBER_OF_RATINGS",
    "AVERAGE_RATING_FOR_VERSION",
    "NUMBER_OF_RATINGS_FOR_VERSION",
    "ORIGINAL_RELEASE_DATE",
    "CURRENT_VERSION_RELEASE_DATE",
    "PRICE_USD" FLOAT,
    "PRIMARY_GENRE",
    "ALL_GENRES",
    "LANGUAGES",
    "DESCRIPTION"
    """


def read_data(ti: TaskInstance) -> bool:
    """read csv file"""
    data = pd.read_csv(CSV_FILE)

    data.columns = map(lambda x: str(x).upper(), data.columns)

    ti.xcom_push("data", data.to_json())
    return True


def create_tables_and_streams() -> bool:
    """Create tables and streams"""
    create_raw_table = f"""CREATE OR REPLACE TABLE
        {DATABASE}.{SCHEMA}.RAW_TABLE ({table_schema})"""

    cursor.execute(create_raw_table)

    cursor.execute("CREATE OR REPLACE TABLE STAGE_TABLE LIKE RAW_TABLE")
    cursor.execute("CREATE OR REPLACE TABLE MASTER_TABLE LIKE STAGE_TABLE")

    cursor.execute("CREATE OR REPLACE STREAM RAW_STREAM ON TABLE RAW_TABLE")
    cursor.execute("CREATE OR REPLACE STREAM STAGE_STREAM ON TABLE STAGE_TABLE")
    return True


def write_to_snowflake(ti: TaskInstance) -> bool:
    """Write data to snowflake"""
    data = ti.xcom_pull(task_ids="read_data", key="data")

    data = pd.read_json(data)

    snowflake.connector.pandas_tools.write_pandas(connection, data, table_name='RAW_TABLE')
    return True


def insert_to_stage_table() -> bool:
    """Insert data into STAGE_TABLE from stream"""
    cursor.execute(f"INSERT INTO STAGE_TABLE (SELECT {column_names} FROM RAW_STREAM)")
    return True


def insert_to_master_table() -> bool:
    """Insert data into MASTER_TABLE from stream"""
    cursor.execute(f"INSERT INTO MASTER_TABLE (SELECT {column_names} FROM STAGE_STREAM)")
    cursor.close()
    return True


with DAG(
        dag_id='snowflake_dag',
        start_date=datetime(year=2022, month=7, day=28),
        schedule_interval='@daily',
        catchup=False
) as dag:
    t1 = PythonOperator(
        task_id='read_data',
        python_callable=read_data,
    )

    t2 = PythonOperator(
        task_id='create_tables_and_streams',
        python_callable=create_tables_and_streams,
    )

    t3 = PythonOperator(
        task_id='write_to_snowflake',
        python_callable=write_to_snowflake,
    )

    t4 = PythonOperator(
        task_id='insert_to_stage_table',
        python_callable=insert_to_stage_table,
    )

    t5 = PythonOperator(
        task_id='insert_to_master_table',
        python_callable=insert_to_master_table,
    )

    [t1, t2] >> t3 >> t4 >> t5
