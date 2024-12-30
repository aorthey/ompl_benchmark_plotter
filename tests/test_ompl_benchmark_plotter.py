import pytest
from src.database_info import *
from src.database_to_graph import *
from src.get_diverse_color import *
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

def test_get_diverse_colors():
  c1 = get_diverse_color("first")
  c2 = get_diverse_color("second")
  c3 = get_diverse_color("third")
  c4 = get_diverse_color("first")
  c5 = get_diverse_color("second")
  assert c1 == c4
  assert c1 != c2
  assert c1 != c3
  assert c2 == c5
  assert c2 != c4

def test_remove_nonoptimal_planners():
  database_filepath = "tests/data/example.db"
  connection = sqlite3.connect(database_filepath)
  assert connection is not None
  cursor = connection.cursor()
  assert cursor is not None

  planners = cursor.execute("SELECT id, name, settings FROM {}".format('plannerConfigs')).fetchall()
  assert len(planners) == 8
  planners_optimal = remove_non_optimal_planner(cursor, planners)
  assert len(planners_optimal) == 3

def test_remove_nonoptimal_planners_simple():
  database_filepath = "tests/data/simple.db"
  connection = sqlite3.connect(database_filepath)
  assert connection is not None
  cursor = connection.cursor()
  assert cursor is not None

  planners = cursor.execute("SELECT id, name FROM {}".format('plannerConfigs')).fetchall()
  assert len(planners) == 5
  planners_optimal = remove_non_optimal_planner(cursor, planners)
  assert len(planners_optimal) == 2

def test_raise_exception_on_non_existing_file():
  with pytest.raises(Exception):
    run_benchmark_plotter(["tests/data/UnKnOwN.db", "-q"])

def test_raise_exception_on_non_database_file():
  non_db_file = "tests/data/UnKnOwN.txt"
  assert not os.path.isfile(non_db_file)
  file = open(non_db_file, "w+")
  assert os.path.isfile(non_db_file)
  with pytest.raises(Exception):
    run_benchmark_plotter([non_db_file, "-q"])
  os.remove(non_db_file)
  assert not os.path.isfile(non_db_file)

def test_raise_exception_on_empty_database_file():
  non_db_file = "tests/data/UnKnOwN.db"
  assert not os.path.isfile(non_db_file)
  file = open(non_db_file, "w+")
  assert os.path.isfile(non_db_file)
  with pytest.raises(Exception):
    run_benchmark_plotter([non_db_file, "-q"])
  os.remove(non_db_file)
  assert not os.path.isfile(non_db_file)

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

