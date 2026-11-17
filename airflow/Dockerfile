FROM apache/airflow:3.4.0
# same tag as docker-compose.yaml

RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" \
    apache-airflow-providers-amazon apache-airflow-providers-snowflake

# dbt in its own venv so its dependencies don't clash with Airflow's
RUN python -m venv /home/airflow/dbt_venv \
    && /home/airflow/dbt_venv/bin/pip install --no-cache-dir dbt-snowflake