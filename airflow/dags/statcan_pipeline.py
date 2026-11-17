from datetime import datetime
from pathlib import Path

from airflow.sdk import dag, task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.bash import BashOperator

BUCKET = "stats-canada-grocery-data"
DATA_DIR = Path("/opt/airflow/data/loading")
YEARS = [2025, 2026]

# S3 dataset name -> (local folder, file prefix, Snowflake table)
DATASETS = {
    "average-price": ("average-price", "average-price", "SOURCE_AVERAGE_PRICE"),
    "cpi": ("province-wise", "provience-price", "SOURCE_CPI"),
}


@dag(schedule=None, start_date=datetime(2026, 1, 1), catchup=False, tags=["statcan"])
def statcan_pipeline():

    @task
    def upload(dataset: str, folder: str, prefix: str, year: int):
        local = DATA_DIR / folder / f"{prefix}_{year}.csv"
        key = f"landing/{dataset}/year={year}/{local.name}"
        S3Hook(aws_conn_id="aws_default").load_file(
            str(local), key, bucket_name=BUCKET, replace=True
        )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            "cd /opt/airflow/statscan_dbt && "
            "/home/airflow/dbt_venv/bin/dbt build --profiles-dir /opt/airflow/dbt"
        ),
    )

    for year in YEARS:
        for dataset, (folder, prefix, table) in DATASETS.items():
            up = upload.override(task_id=f"upload_{dataset}_{year}")(dataset, folder, prefix, year)
            load = SQLExecuteQueryOperator(
                task_id=f"load_{dataset}_{year}",
                conn_id="snowflake_default",
                sql=[
                    # delete first so a re-run never duplicates rows
                    f"DELETE FROM STATSCAN_ANALYTICS.SOURCE.{table} WHERE REF_DATE LIKE '{year}%'",
                    f"""COPY INTO STATSCAN_ANALYTICS.SOURCE.{table}
                        FROM @STATSCAN_ANALYTICS.SOURCE.STATSCAN_S3_STAGE/{dataset}/year={year}/
                        FILE_FORMAT = (FORMAT_NAME = 'STATSCAN_ANALYTICS.SOURCE.STATSCAN_CSV')
                        MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
                        FORCE = TRUE""",
                ],
            )
            up >> load >> dbt_build


statcan_pipeline()