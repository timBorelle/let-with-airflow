import pytest

import airflow
from airflow import DAG
from airflow.models import DagBag


@pytest.fixture()
def dagbag():
    return DagBag()

# Unit test for loading a DAG
def test_dag_loaded(dagbag):
    dag = dagbag.get_dag(dag_id="let_data")
    assert dagbag.import_errors == {}
    assert dag is not None
    assert len(dag.tasks) == 5

#test_dag_loaded(dagbag)