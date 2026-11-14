"""Validate the scheduler graph without starting Airflow or accessing a database."""

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec('airflow'), 'Airflow is optional')
class DagTests(unittest.TestCase):
    def test_each_player_has_extract_process_load_dependencies(self):
        with tempfile.TemporaryDirectory(prefix='bauchess-airflow-') as home:
            with patch.dict(os.environ, {'AIRFLOW_HOME': home, 'AIRFLOW__CORE__LOAD_EXAMPLES': 'False'}):
                from airflow.models.dagbag import DagBag
                with patch('config.read_people', return_value=['Alice', 'Bob']):
                    bag = DagBag(dag_folder=str(Path(__file__).resolve().parents[1] / 'Dags'), include_examples=False)
        self.assertEqual(bag.import_errors, {})
        dag = bag.dags['BauChess_Scrap_to_DB']
        self.assertEqual(len(dag.tasks), 6)
        self.assertEqual(dag.max_active_runs, 1)
        for index in range(2):
            prefix = f'player_{index}.'
            self.assertEqual(dag.get_task(prefix + 'process').upstream_task_ids, {prefix + 'extract'})
            self.assertEqual(dag.get_task(prefix + 'load').upstream_task_ids, {prefix + 'process'})
            self.assertEqual(dag.get_task(prefix + 'extract').retries, 3)


if __name__ == '__main__':
    unittest.main()
