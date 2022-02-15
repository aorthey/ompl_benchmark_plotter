import json
import os
import numpy as np
import sqlite3
from pathlib import Path
from src.plot_style import *

def get_tables_from_database(cursor):
  tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
  for table in tables:
      cursor.execute("SELECT * FROM {}".format(table[0])).fetchall()
      names = list(map(lambda x: x[0], cursor.description))
      print("\nTable \'{}\': {}".format(table[0], names))

def combine_planner_data(planner_data1, planner_data2):
  if planner_data1 is None:
    return planner_data2
  if planner_data2 is None:
    return planner_data1

  planner_data = {}
  best_time = float("inf")
  best_planner = ""
  for name1 in planner_data1: 
    found = False
    for name2 in planner_data2: 
      if name1 == name2:
        t1 = planner_data1[name1]['time_mean']
        t2 = planner_data2[name2]['time_mean']
        time_limit = planner_data1[name1]['time_limit']
        s1 = planner_data1[name1]['time_variance']
        s2 = planner_data2[name2]['time_variance']
        time_variance = np.std([s1, s2])
        time_mean = np.mean([t1, t2])
        n1 = planner_data1[name1]['number_runs']
        n2 = planner_data2[name2]['number_runs']
        number_runs = n1 + n2
        su1 = planner_data1[name1]['success']
        su2 = planner_data2[name2]['success']
        success = 0.5*(su1 + su2)
        planner_data[name1] = { 'time_mean' : time_mean, 'time_limit':
            time_limit, 'time_variance' : time_variance, 'success' : success,
            'best_planner' : False,
            'number_runs' : number_runs }
        found = True
        if time_mean < best_time:
          best_time = time_mean
          best_planner = name1
        break
    if not found:
      planner_data[name1] = planner_data1[name1]
  if best_time < float("inf"):
    planner_data[best_planner]['best_planner'] = True
  return planner_data

def get_experiment_names_from_database(cursor):
  experiments = cursor.execute("SELECT id, name FROM {}".format('experiments')).fetchall()
  experiment_names = []
  for experiment in experiments:
      experiment_name = experiment[1]
      experiment_names.append("Experiment {} [ID {}]".format(experiment[1], experiment[0]))
  return experiment_names

def get_experiment_name_from_array(experiment_names):
  if len(experiment_names) < 1:
    return "unknown"
  else:
    return experiment_names[0]

def assert_equivalent_experiment_names(cursor):
  experiments = cursor.execute("SELECT id, name FROM {}".format('experiments')).fetchall()
  if len(experiments) > 0:
    name = experiments[0][1]
    for experiment in experiments:
      next_name = experiment[1]
      if not (name == next_name):
        return False

  return True

def get_experiment_names_from_database(cursor):
  experiments = cursor.execute("SELECT id, name FROM {}".format('experiments')).fetchall()
  experiment_names = []
  for experiment in experiments:
      experiment_name = experiment[1]
      # experiment_names.append("Experiment {} [ID {}]".format(experiment[1], experiment[0]))
      experiment_names.append(experiment_name)
  return experiment_names

def get_longest_name_from_experiments(names):
  longest_name = ""
  for name in names:
    name = get_experiment_label(name)
    if len(name) > len(longest_name) :
      longest_name = name
  return longest_name

def get_longest_name_from_planners(names):
  longest_name = ""
  for name in names:
    name = get_label(name)
    if len(name) > len(longest_name) :
      longest_name = name
  return longest_name

def get_time_limit_for_experiment(cursor, experiment_id):
  return cursor.execute("SELECT timelimit FROM {} WHERE id={}".format('experiments',experiment_id)).fetchall()[0][0]


def get_planner_names_from_database(cursor):
  planners = cursor.execute("SELECT id, name FROM {}".format('plannerConfigs')).fetchall()
  planner_names = []
  for planner in planners:
      planner_names.append(planner[1])
  return planner_names

def has_best_cost(cursor):
  cursor.execute("SELECT * FROM {}".format('progress')).fetchall()
  names = list(map(lambda x: x[0], cursor.description))
  return True if 'best_cost' in names else False

def get_run_results_from_database(cursor):
  planners = cursor.execute("SELECT id, name FROM {}".format('plannerConfigs')).fetchall()
  for planner in planners:
    planner_id = planner[0]
    getids = cursor.execute("SELECT id FROM {} WHERE plannerid={}".format('runs',planner_id)).fetchall()
    runs = np.array(getids).flatten()
    runids = ','.join(str(run) for run in runs)
    if has_best_cost(cursor):
      data = np.array(cursor.execute("SELECT time, best_cost FROM {} WHERE runid in ({})".format('progress', runids)).fetchall()).flatten()

  for planner in planners:
    planner_id = planner[0]
    getids = cursor.execute("SELECT id FROM {} WHERE plannerid={}".format('runs',planner_id)).fetchall()
    runs = np.array(getids).flatten()
    runids = ','.join(str(run) for run in runs)
    if has_best_cost(cursor):
      data = np.array(cursor.execute("SELECT time, best_cost FROM {} WHERE runid in ({})".format('progress', runids)).fetchall()).flatten()
      if len(data) > 0:
        print("Planner {} with time {} and cost {}".format(planner[1], data[0], data[1]))


def get_filename_from_database_filepaths(filepaths):
  if len(filepaths) <= 0:
    return "unknown"
  filepath = filepaths[0]
  directory = os.path.dirname(filepath)
  filename_without_extension =  directory + "/" + "runtime_table"
  return filename_without_extension

def create_filename_with_extension(filename_without_extension, extension):
  i = 0
  path_exist = True
  while path_exist:
    filename = filename_without_extension + ("%s%s"%(i,extension))
    path_exist = os.path.exists(filename)
    i += 1
  return filename

def get_pdf_from_database_filepaths(filepaths):
  filename_without_extension = get_filename_from_database_filepaths(filepaths)
  return create_filename_with_extension(filename_without_extension, ".pdf")

def get_tex_from_database_filepaths(filepaths):
  filename_without_extension = get_filename_from_database_filepaths(filepaths)
  return create_filename_with_extension(filename_without_extension, ".tex")

def get_cell_entry(data, experiment, planner, hide_variance=False):
  time = data['experiments'][experiment][planner]['time_mean']
  timelimit = data['experiments'][experiment][planner]['time_limit']
  if time > timelimit:
    time = timelimit

  var = data['experiments'][experiment][planner]['time_variance']
  best = data['experiments'][experiment][planner]['best_planner']
  number_runs = data['experiments'][experiment][planner]['number_runs']

  cell_entry = "$"
  if best:
    cell_entry += "\\textbf{%.2f}"%(time)
  else:
    cell_entry += "%.2f"%(time)
  if not hide_variance:
    cell_entry += "\\color{gray}{\\pm %.2f}"%(var)
  cell_entry += "$"
  return cell_entry

def get_json_filepath_from_databases(filepaths): 
  filename_without_extension = get_filename_from_database_filepaths(filepaths)
  return create_filename_with_extension(filename_without_extension, ".json")

def change_filename_extension(filepath, extension):
  filepath_without_extension = os.path.splitext(filepath)[0]
  return filepath_without_extension + extension

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


def is_planner_optimal(planner):
  name = get_label(planner)
  if name == "RRT":
    return False
  elif name == "RRTConnect":
    return False
  elif name == "PRM":
    return False
  elif name == "EST":
    return False
  elif name == "BiEST":
    return False
  elif name == "RLRT":
    return False
  elif name == "BiRLRT":
    return False
  elif name == "TRRT":
    return False
  elif name == "BiTRRT":
    return False
  elif name == "FMT":
    return False
  elif name == "BFMT":
    return False
  else:
    return True

def remove_non_optimal_planner(planners):
  return [x for x in planners if is_planner_optimal(x[1])]

def load_config():
    cwd = Path(__file__).parent.absolute()
    json_config = "{}/../config/default.json".format(cwd)
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
