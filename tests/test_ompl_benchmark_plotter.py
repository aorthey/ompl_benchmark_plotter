import pytest
from src.database_info import *
from src.database_to_graph import *
from ompl_benchmark_plotter import *
import os.path

def test_load_simple_database():
  database_filepath = "tests/data/simple.db"
  assert os.path.isfile(database_filepath)

  connection = sqlite3.connect(database_filepath)
  assert connection is not None
  cursor = connection.cursor()
  assert cursor is not None

  ## Check if the database has the correct entries
  assert has_solution_length(cursor)
  assert has_best_cost(cursor)

  ## Check if we loaded the correct number of planners and experiments
  experiment_names = get_experiment_names_from_database(cursor)
  assert len(experiment_names) == 1
  planner_names = get_planner_names_from_database(cursor)
  assert len(planner_names) == 5

  ## Check specific entries are loaded correctly
  assert get_maxtime_from_database(cursor) == pytest.approx(10.0)
  assert get_longest_name_from_planners(planner_names) == "RRTConnect"

def test_load_default_config():
  data = load_config()
  assert data is not None
  assert data["max_cost"] > 0.0
  assert data["min_cost"] >= 0.0
  assert data["min_cost"] <= data["max_cost"]
  assert data.get("final_cost") is None

def test_verify_graph_plotting_from_simple_database():
  pdffile = "tests/data/simple.pdf"
  assert not os.path.isfile(pdffile)
  assert run_benchmark_plotter(["tests/data/simple.db", "-q"]) == 0
  assert os.path.isfile(pdffile)
  os.remove(pdffile)
  assert not os.path.isfile(pdffile)

def test_verify_graph_plotting_from_example_database():
  pdffile = "tests/data/example.pdf"
  assert not os.path.isfile(pdffile)
  assert run_benchmark_plotter(["tests/data/example.db", "-q"]) == 0
  assert os.path.isfile(pdffile)
  os.remove(pdffile)
  assert not os.path.isfile(pdffile)

def test_invalid_files():
  with pytest.raises(Exception):
    run_benchmark_plotter(["tests/data/UnKnOwN.db", "-q"])


