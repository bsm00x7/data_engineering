from  airflow import DAG

from  airflow.providers.standard.operators.python import  PythonOperator

from  datetime import  datetime
# schedule="@once"      # Run only once
# schedule="@hourly"    # Every hour
# schedule="@daily"     # Every day
# schedule="@weekly"    # Every week
# schedule="@monthly"   # Every month
# schedule="@yearly"    # Every year

def task1 ():
    print(f"Hello This First Tasks in date {datetime.fromisoformat}")
def task2 ():
    print(f"Hello This First Tasks in date {datetime.fromisoformat}")
def task3 ():
    print(f"Hello This First Tasks in date {datetime.fromisoformat}")
with DAG(
    dag_id="Scheduler_with_docker",
    start_date=datetime(2026,1,1),
    schedule="@once",
    catchup=False
) as dg:
    task1 = PythonOperator(
        task_id="1",
        python_callable=task1
    )
    task2 = PythonOperator(
        task_id="2",
        python_callable=task2
    )
    task3 = PythonOperator(
        task_id="3",
        python_callable=task3
    )
