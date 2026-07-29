from datetime import datetime
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

# Since your main module is in dags folder, you need to import it properly
import sys
import os

from main import FraudDetectionSupervised

sys.path.insert(0, os.path.dirname(__file__))



with DAG(
    dag_id="fraud_detection_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@once",
    catchup=False,
    tags=["fraud", "ml"],
    description="Fraud Detection Training Pipeline using MinIO for data exchange",
) as dag:

    # Instantiate the trainer - methods are stateless, safe for distributed execution
    trainer = FraudDetectionSupervised()

    check_task = PythonOperator(
        task_id="check_data",
        python_callable=trainer.checkData,  # No parentheses - pass callable
        doc="Validate the raw dataset exists and is readable",
    )

    clean_task = PythonOperator(
        task_id="clean_data_task",
        python_callable=trainer.cleanData,
        doc="Clean data, engineer features, and upload to MinIO",
    )

    train_task = PythonOperator(
        task_id="train_model_task",
        python_callable=trainer.training,
        doc="Download cleaned data from MinIO, train model, and upload artifact",
    )

    check_task >> clean_task >> train_task