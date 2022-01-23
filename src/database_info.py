import json
import sqlite3

def get_tables_from_database(cursor):
  tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
  for table in tables:
      cursor.execute("SELECT * FROM {}".format(table[0])).fetchall()
      names = list(map(lambda x: x[0], cursor.description))
      print("\nTable \'{}\': {}".format(table[0], names))


def get_experiment_names_from_database(cursor):
  experiments = cursor.execute("SELECT id, name FROM {}".format('experiments')).fetchall()
  experiment_names = []
  for experiment in experiments:
      experiment_name = experiment[1]
      # print("Experiment {} has ID {}".format(experiment[1], experiment[0]))
      experiment_names.append(experiment_name)
  return experiment_names

def get_planner_names_from_database(cursor):
  planners = cursor.execute("SELECT id, name FROM {}".format('plannerConfigs')).fetchall()
  planner_names = []
  for planner in planners:
      planner_names.append(planner[1])
  return planner_names

def print_metadata_from_database(cur):
  print(80*"-")
  print("-- Tables in database file")
  print(80*"-")
  print(get_tables_from_database(cur))
  print(80*"-")
  print("-- Planner in database")
  print(80*"-")
  print(get_planner_names_from_database(cur))
  print(80*"-")
  print("-- Experiments in database")
  print(80*"-")
  print(get_experiment_names_from_database(cur))

def load_config():
    json_config = "config/default.json"
    with open(json_config, 'r') as jsonfile:
        info = json.load(jsonfile)
    return info

def get_average_runtime_from_database(cur, data):
  print("NYI")

############################################################
### Print All Runs
############################################################
# print(80*"-")
# print("-- Runs in database")
# print(80*"-")

# runs = cur.execute("SELECT id, experimentid, plannerid, correct_solution, time, best_cost FROM {}".format('runs')).fetchall()
# for run in runs:
#   print("Run {} on environment {} with planner {}. Correct solution:{}. Time {}".format(run[0], run[1], run[2], run[3], run[4]))
