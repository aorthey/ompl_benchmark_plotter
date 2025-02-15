import json
import os
import sys
import numpy as np
import sqlite3
from itertools import repeat
from pathlib import Path
from src.get_plot_style import *

def get_cost_results(cursor, runids, times, max_cost, ci_left, ci_right):
    medians = np.zeros(len(times))
    quantile5 = np.zeros(len(times))
    quantile95 = np.zeros(len(times))

    improvement = False
    for i in range(len(times)):
        data = np.array(cursor.execute("SELECT a.best_cost FROM (SELECT MAX(time), \
          best_cost FROM {0} WHERE time<={1} AND runid in ({2}) GROUP BY runid) a".format('progress', times[i], runids)).fetchall()).flatten()
        if data.size == 0:
            medians[i] = max_cost
            quantile5[i] = max_cost
            quantile95[i] = max_cost
        else:
            data = np.where(data == None, max_cost, data)
            medians[i] = np.median(data)
            quantile5[i] = np.percentile(data, ci_left, interpolation='nearest')
            quantile95[i] = np.percentile(data, ci_right, interpolation='nearest')
            improvement = True

    return [improvement, medians, quantile5, quantile95]

def is_planner_optimal(cursor, planner_id):
  getids = cursor.execute("SELECT id FROM {} WHERE plannerid={}".format('runs', planner_id)).fetchone()
  runid = getids[0]
  data = cursor.execute("SELECT time, best_cost FROM {} WHERE runid in ({})".format('progress', runid)).fetchall()
  if data is None:
    return False
  return len(data) > 10

def remove_non_optimal_planner(cursor, planners):
  if not has_best_cost(cursor):
    return []
  return [x for x in planners if is_planner_optimal(cursor, x[0])]

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

def get_maxtime_from_database(cursor):
  times = cursor.execute("SELECT timelimit FROM {}".format('experiments')).fetchall()
  times = np.array(times).flatten()
  return times.max()

def get_maxtime_from_database_or_config(cursor, config, data):
  if config['max_time'] > 0:
    time = config['max_time']
  else:
    time = get_maxtime_from_database(cursor)

  data["info"]['max_time']['success'] = time
  data["info"]['max_time']['optimization'] = time
  return time

def get_mintime_from_database_or_config(cursor, config, data):
  kDefaultTimeDifferenceOrderOfMagnitude = 3
  if config['min_time'] > 0:
    time = config['min_time']
  else:
    maxtime = float(get_maxtime_from_database_or_config(cursor, config, data))
    oom = int(np.floor(np.log10(maxtime)))
    time = 10**(oom-kDefaultTimeDifferenceOrderOfMagnitude)

  data["info"]['min_time']['success'] = time
  data["info"]['min_time']['optimization'] = time
  return time

def get_start_index(medians, times, max_cost):
    for i in range(len(times)):
        if medians[i] < max_cost:
            return i
    return len(times)

def get_maxcost_from_json_or_config(data, config, times):
  kPercentagePaddingAboveMax = 0.1
  max_cost_in_data_acquisition = data["info"]["max_cost"]
  max_cost = 0
  if config['max_cost'] > 0:
    max_cost = config['max_cost']
  else:
    planner_data = data["planners"]
    for planner in planner_data:
      ycost = max_cost_in_data_acquisition
      planner_optimization_success = planner_data[planner]["optimization_success"]
      if planner_optimization_success:
        planner_median = planner_data[planner]["median"]
        start = get_start_index(planner_median, times, max_cost_in_data_acquisition)
        cost_below_max = planner_median[start:]
        if len(cost_below_max) > 0:
          ycost = np.array(cost_below_max).max()
      else:
        planner_point = planner_data[planner]["point"]
        ycost = planner_point["cost"][0]
      if ycost > max_cost:
        if ycost < max_cost_in_data_acquisition:
          max_cost = ycost
    max_cost = max_cost + kPercentagePaddingAboveMax*max_cost

  data["info"]["max_cost"] = max_cost
  return max_cost

def get_mincost_from_json_or_config(data, config, times, max_cost):
  kPercentagePaddingBelowMin = 0.1
  min_cost = max_cost
  if config['min_cost'] > 0:
    min_cost = config['min_cost']
  else:
    planner_data = data["planners"]
    for planner in planner_data:
      planner_optimization_success = planner_data[planner]["optimization_success"]
      if planner_optimization_success:
        planner_median = planner_data[planner]["median"]
        ycost = np.array(planner_median).min()
      else:
        planner_point = planner_data[planner]["point"]
        ycost = planner_point["cost"][0]
      if ycost < min_cost:
        min_cost = ycost

  dc = max_cost - min_cost
  min_cost = np.maximum(0.0, min_cost - kPercentagePaddingBelowMin*dc)
  data["info"]["min_cost"] = min_cost
  return min_cost

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

def has_table_column(cursor, table_name, column_name):
  cursor.execute("SELECT * FROM {}".format(table_name)).fetchall()
  names = list(map(lambda x: x[0], cursor.description))
  return True if column_name in names else False

def has_solution_length(cursor):
  return has_table_column(cursor, 'runs', 'solution_length')

def has_best_cost(cursor):
  return has_table_column(cursor, 'progress', 'best_cost')

def get_filename_from_database_filepaths_and_name(filepaths, name):
  if len(filepaths) <= 0:
    return "unknown"
  filepath = filepaths[0]
  directory = os.path.dirname(filepath)
  if len(directory) > 0:
    directory += "/"
  filename = directory + name
  return filename

def get_filename_from_database_filepaths(filepaths):
  if len(filepaths) <= 0:
    return "unknown"
  filepath = filepaths[0]
  directory = os.path.dirname(filepath)
  filename = os.path.splitext(os.path.basename(filepath))[0]
  if len(directory) > 0:
    directory += "/"

  filename_without_extension =  directory + filename
  return filename_without_extension

def create_filename_with_extension(filename_without_extension, extension):
  i = 0
  filename = filename_without_extension + ("%s"%(extension))
  path_exist = os.path.exists(filename)
  if path_exist:
    print("Warning: overwriting file %s."%(filename))
  return filename

def get_pdf_from_database_filepaths(filepaths):
  filename_without_extension = get_filename_from_database_filepaths(filepaths)
  return create_filename_with_extension(filename_without_extension, ".pdf")

def get_json_filepath_from_databases(filepaths): 
  filename_without_extension = get_filename_from_database_filepaths(filepaths)
  return create_filename_with_extension(filename_without_extension, ".json")

def change_filename_extension(filepath, extension):
  filepath_without_extension = os.path.splitext(filepath)[0]
  return filepath_without_extension + extension

def create_time_space(data):
  return np.logspace(np.log10(data["info"]["min_time"]["success"]), \
      np.log10(data["info"]["max_time"]["success"]), \
                      data["info"]["resolution"])

def create_time_space_linear(data):
  return np.linspace(0, data["info"]["timelimit"], \
                      data["info"]["resolution_linear"])

def get_times_from_success_over_time(success, timespace):
  # input: number of successes for each time element
  all_count = 0
  times = []
  for (count, time) in zip(success, timespace):
    Nitems = int(count - all_count)
    if Nitems > 0:
      times.extend(repeat(time, Nitems))
      all_count = count
  ## add last time element to fill it up for unsuccessful runs
  if len(times) < 100:
    times.extend(repeat(time, 100-len(times)))
  times = np.array(times)
  return times

def get_count_success(cursor, run_count, runids, times):
    success = np.zeros(len(times))
    for i in range(len(times)):
        ### Select from one time slice all best costs
        data = np.array(cursor.execute("SELECT a.best_cost FROM (SELECT MAX(time), \
              best_cost FROM {0} WHERE time<={1} AND runid in ({2}) GROUP BY runid) a".format('progress', times[i], runids)).fetchall()).flatten()
        if data.size == 0:
            success[i] = 0
        else:
            sum_not_none = sum(x is not None for x in data)
            success[i] = (sum_not_none / run_count ) * 100.0

    return success

def load_config():
    cwd = Path(__file__).parent.absolute()
    json_config = "{}/../config/default.json".format(cwd)
    with open(json_config, 'r') as jsonfile:
        info = json.load(jsonfile)
    return info

def get_average_runtime_from_database(cursor, data):
  raise Exception("NYI")

############################################################
### Print All Runs
############################################################
# print(80*"-")
# print("-- Runs in database")
# print(80*"-")

# runs = cursor.execute("SELECT id, experimentid, plannerid, correct_solution, time, best_cost FROM {}".format('runs')).fetchall()
# for run in runs:
#   print("Run {} on environment {} with planner {}. Correct solution:{}. Time {}".format(run[0], run[1], run[2], run[3], run[4]))

def print_run_results_from_database(cursor):
  planners = cursor.execute("SELECT id, name FROM {}".format('plannerConfigs')).fetchall()
  for planner in planners:
    planner_id = planner[0]
    getids = cursor.execute("SELECT id FROM {} WHERE plannerid={}".format('runs',planner_id)).fetchall()
    runs = np.array(getids).flatten()
    runids = ','.join(str(run) for run in runs)

    exp_getids = cursor.execute("SELECT id FROM {}".format('experiments')).fetchall()
    exps = np.array(exp_getids).flatten()
    expids = ','.join(str(exp) for exp in exps)

    print("Run ids {}".format(runids))
    print("Exp ids {}".format(expids))

    if has_best_cost(cursor):
      data = np.array(cursor.execute("SELECT time, best_cost FROM {} WHERE runid in ({})".format('progress', runids)).fetchall()).flatten()
      if len(data) > 0:
        print("Planner {} with time {} and cost {}".format(planner[1], data[0], data[1]))
    else:
      data = np.array(cursor.execute("SELECT time FROM {} WHERE id in ({}) and \
        experimentid in ({})".format('runs', runids, expids)).fetchall()).flatten()
      print("Planner {} with time {}".format(planner[1], np.around(data)))

  for planner in planners:
    planner_id = planner[0]
    getids = cursor.execute("SELECT id FROM {} WHERE plannerid={}".format('runs',planner_id)).fetchall()
    runs = np.array(getids).flatten()
    runids = ','.join(str(run) for run in runs)
    if has_best_cost(cursor):
      data = np.array(cursor.execute("SELECT time, best_cost FROM {} WHERE runid in ({})".format('progress', runids)).fetchall()).flatten()
      if len(data) > 0:
        print("Planner {} with time {} and cost {}".format(planner[1], data[0], data[1]))

def print_metadata_from_database(cursor):
  print(80*"-")
  print("-- Tables in database file")
  print(80*"-")
  print(get_tables_from_database(cursor))
  print(80*"-")
  print("-- Planner in database")
  print(80*"-")
  print(get_planner_names_from_database(cursor))
  print(80*"-")
  print("-- Experiments in database")
  print(80*"-")
  print(get_experiment_names_from_database(cursor))

def make_config(args):
  max_cost = args.max_cost if args.max_cost else -1
  min_cost = args.min_cost if args.min_cost else -1
  max_time = args.max_time if args.max_time else -1
  min_time = args.min_time if args.min_time else -1
  fontsize = args.fontsize if args.fontsize else -1
  only_success_graph = args.only_success_graph if args.only_success_graph else False
  label_fontsize = args.label_fontsize if args.label_fontsize else -1
  plot_config = {
      'show': args.show,
      'only_success_graph': args.only_success_graph,
      'output_file': args.output_file,
      'verbosity': args.verbose,
      'max_cost': max_cost,
      'min_cost': min_cost,
      'max_time': max_time,
      'min_time': min_time,
      'fontsize': fontsize,
      'label_fontsize': label_fontsize,
      'ignore_non_optimal_planner': args.ignore_non_optimal_planner,
      'legend_below_figure': args.legend_below_figure,
      'legend_separate_file': args.legend_separate_file,
      'legend_none': args.legend_none
  }
  if args.title_name:
    plot_config['title_name'] = args.title_name
  return plot_config
