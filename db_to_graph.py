import sys
import json
import os
import sqlite3
import numpy as np
import matplotlib.pyplot as plt

info = {
        "alpha_percentile": 0.4,
        "resolution": 200,
        "min_time": {
            "success": 0.001,
            "optimization": 0.001
        },
        "max_time": {
            "success": 30,
            "optimization": 30
        },
        "max_cost": 100,
        "ci_left": 39,
        "ci_right": 59
}


print('Number of arguments:', len(sys.argv), 'arguments.')
print('Argument List:', str(sys.argv))

def GetMarker(planner_name):
  return "x"

def GetLineStyle(planner_name):
  return "-"

def GetLabel(planner_name):
  name = planner_name.lstrip("geometric_")
  return name

def GetColor(planner_name):
  name = GetLabel(planner_name)
  if name == "FMT":
    return "gray"
  if name == "BFMT":
    return "black"
  if name == "RRTConnect":
    return "red"
  if name == "RRT":
    return "cyan"
  if name == "LBTRRT":
    return "orange"
  if name == "kBITstar":
    return "blue"
  if name == "RRTstar":
    return "purple"
  if name == "KPIECE1":
    return "green"
  return "red"

def get_cost_results(cur, runids, times, max_cost, ci_left, ci_right):
    medians = np.zeros(len(times))
    quantile5 = np.zeros(len(times))
    quantile95 = np.zeros(len(times))

    improvement = False
    for i in range(len(times)):
        data = np.array(cur.execute("SELECT a.best_cost FROM (SELECT MAX(time), \
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

def get_count_success(cur, runids, times, max_cost, ci_left, ci_right):
    success = np.zeros(len(times))

    for i in range(len(times)):
        data = np.array(cur.execute("SELECT a.best_cost FROM (SELECT MAX(time), \
          best_cost FROM {0} WHERE time<={1} AND runid in ({2}) GROUP BY runid) a".format('progress', times[i], runids)).fetchall()).flatten()
        if data.size == 0:
            success[i] = 0
        else:
            success[i] = (sum(x is not None for x in data))

    return success

def PrintInfo(filepath, data):

  con = sqlite3.connect(filepath)
  cur = con.cursor()

  ############################################################
  ### Print All Tables
  ############################################################
  tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
  print(80*"-")
  print("-- Tables in database file {}".format(filepath))
  print(80*"-")
  for table in tables:
      cur.execute("SELECT * FROM {}".format(table[0])).fetchall()
      names = list(map(lambda x: x[0], cur.description))
      print("\nTable \'{}\': {}".format(table[0], names))
      # for name in names: 
      #   outputs = cur.execute("SELECT {} FROM {}".format(name, table[0])).fetchall()
      #   print(outputs)
  
  ############################################################
  ### Print All Planner
  ############################################################
  print(80*"-")
  print("-- Planner in database")
  print(80*"-")
  planners = cur.execute("SELECT id, name FROM {}".format('plannerConfigs')).fetchall()
  for planner in planners:
      print("Planner {} has ID {}".format(planner[1], planner[0]))

  ############################################################
  ### Print All Experiments
  ############################################################
  print(80*"-")
  print("-- Experiments in database")
  print(80*"-")
  experiments = cur.execute("SELECT id, name FROM {}".format('experiments')).fetchall()
  for experiment in  experiments:
      print("Experiment {} has ID {}".format(experiment[1], experiment[0]))

  ############################################################
  ### Print All Runs
  ############################################################
  print(80*"-")
  print("-- Runs in database")
  print(80*"-")

  runs = cur.execute("SELECT id, experimentid, plannerid, correct_solution, time, best_cost FROM {}".format('runs')).fetchall()
  for run in runs:
    print("Run {} on environment {} with planner {}. Correct solution:{}. Time {}".format(run[0], run[1], run[2], run[3], run[4]))

  ############################################################
  ### Print All Best Cost per Run
  ############################################################
  # print(80*"-")
  # print("-- Best cost in database")
  # print(80*"-")
  # # Table 'progress': ['runid', 'time', 'best_cost', 'iterations', 'current_free_states', 'current_graph_vertices', 'edge_collision_checks', 'nearest_neighbour_calls', 'number_of_segments_in_solution_path', 'state_collision_checks']

  # runs = cur.execute("SELECT runid, best_cost FROM {}".format('progress')).fetchall()
  # for run in runs:
  #   print("Run {} with best cost {}".format(run[0], run[1]))

  ############################################################
  ### Print Average Success per Planner over Time
  ############################################################
  print(80*"-")
  print("-- Times for planners ")
  print(80*"-")

  times = np.logspace(np.log10(data["info"]["min_time"]["success"]), np.log10(data["info"]["max_time"]["success"]),
                      data["info"]["resolution"])

  planners = cur.execute("SELECT id, name FROM {}".format('plannerConfigs')).fetchall()
  for planner in planners:
    planner_id = planner[0]
    planner_name = planner[1]
    number_runs = cur.execute("SELECT COUNT(*) FROM {} WHERE plannerid={}".format('runs', planner_id)).fetchall()[0][0]
    print("Planner {} (id {}) has {} runs.".format(planner_name, planner_id, number_runs))

    percentages = np.empty(len(times))
    for i in range(len(times)):
        percentage = cur.execute(
            "SELECT COUNT(*) FROM {0} WHERE plannerid={2} AND time < {1}".format('runs', times[i], planner_id)).fetchall()
        percentages[i] = (percentage[0][0] / number_runs) * 100
    data[planner_name] = {
        "success": percentages.tolist()
        }

    percentages = np.empty(len(times))
    for i in range(len(times)):
        percentage = cur.execute(
            "SELECT COUNT(*) FROM {0} WHERE plannerid={2} AND time < {1}".format('runs', times[i], planner_id)).fetchall()
        percentages[i] = (percentage[0][0] / number_runs) * 100
    data[planner_name] = {
        "success": percentages.tolist()
        }

  ############################################################
  ### Print Cost per Planner over Time
  ############################################################
  print(80*"-")
  print("-- Cost for planners ")
  print(80*"-")

  max_time = data["info"]["max_time"]["optimization"]
  min_time = data["info"]["min_time"]["optimization"]
  times = np.logspace(np.log10(min_time), np.log10(max_time), data["info"]["resolution"])
  max_cost = data["info"]["max_cost"]
  ci_left = data["info"]["ci_left"]
  ci_right = data["info"]["ci_right"]

  for planner in planners:
    planner_id = planner[0]
    planner_name = planner[1]
    getids = cur.execute("SELECT id FROM {} WHERE plannerid={}".format('runs',planner_id)).fetchall()
    runs = np.array(getids).flatten()
    print("Planner Id {} has runs {}".format(planner_id, runs))
    runids = ','.join(str(run) for run in runs)

    results = get_cost_results(cur, runids, times, max_cost, ci_left, ci_right)
    data[planner_name]["optimization_success"] = results[0]
    if results[0]:
      data[planner_name]["median"] = results[1].tolist()
      data[planner_name]["quantile5"] = results[2].tolist()
      data[planner_name]["quantile95"] = results[3].tolist()
      success = get_count_success(cur, runids, times, max_cost, ci_left, ci_right)
      data[planner_name]["success"] = success.tolist()
    else:
      point_data = get_from_runs(cur, planner_id, ci_left, ci_right)
      if point_data is None:
          point_data = max_point(max_time, max_cost)
      data[planner_name]["point"] = point_data


def get_start_index(medians, times, max_cost):
    for i in range(len(times)):
        if medians[i] < max_cost:
            return i
    return len(times)

def get_from_runs(cur, planner_id, ci_left, ci_right):
    pair = np.array(cur.execute("SELECT time, best_cost FROM {0} WHERE plannerid={1} AND status=6".format('runs', planner_id)).fetchall())
    if pair.size == 0:
        return None
    split = np.split(pair, 2, axis=1)
    times = split[0]
    costs = split[1]
    return calculate_points(times, costs, ci_left, ci_right)

def calculate_points(times, costs, ci_left, ci_right):
    if None in costs: 
      return None

    data = {"time": [np.median(times), np.percentile(times, ci_left, interpolation='nearest'),
                     np.percentile(times, ci_right, interpolation='nearest')],
            "cost": [np.median(costs), np.percentile(costs, ci_left, interpolation='nearest'),
                     np.percentile(costs, ci_right, interpolation='nearest')]}
    return data

def max_point(max_time, max_cost):
    data = {"time": [max_time, max_time,
                     max_time],
            "cost": [max_cost, max_cost, max_cost]}
    return data

def get_errors(point):
    time_errors = np.array([[point["time"][0] - point["time"][1]],
                            [point["time"][2] - point["time"][0]]])
    cost_errors = np.array([[point["cost"][0] - point["cost"][1]],
                            [point["cost"][2] - point["cost"][0]]])
    return time_errors, cost_errors


def plot_success(ax, data):

    min_time = data["info"]["min_time"]["success"]
    max_time = data["info"]["max_time"]["success"]
    resolution = data["info"]["resolution"]

    times = np.logspace(np.log10(min_time), np.log10(max_time), resolution)
    ax.set_xscale('log')
    ax.set_yscale('linear')
    ax.set_xlim(min_time, max_time)
    ax.set_ylim(0.0, 100.0)

    for planner in data:
      if planner == "info":
        continue
      print(planner, data[planner])

      success_over_time = data[planner]["success"]
      ax.plot(times, success_over_time, color=GetColor(planner), linestyle=GetLineStyle(planner), label=GetLabel(planner))

    ax.grid(True, which="both", ls='--')
    ax.set_ylabel("success [\%]")

def plot_optimization(ax, data):

    min_time = data["info"]["min_time"]["optimization"]
    max_time = data["info"]["max_time"]["optimization"]
    resolution = data["info"]["resolution"]
    times = np.logspace(np.log10(min_time), np.log10(max_time), resolution)
    max_cost = data["info"]["max_cost"]

    ax.set_xscale('log')
    ax.set_yscale('linear')
    ax.set_xlim(min_time, max_time)
    ax.set_ylim(0.0, max_cost)

    for planner in data:
      if planner == "info":
        continue

      planner_optimization_success = data[planner]["optimization_success"]
      if planner_optimization_success:
        planner_median = data[planner]["median"]
        planner_q5 = data[planner]["quantile5"]
        planner_q95 = data[planner]["quantile95"]

        start = get_start_index(planner_median, times, max_cost)
        ax.plot(times[start:], planner_median[start:], color=GetColor(planner), label=GetLabel(planner))
        ax.fill_between(times[start:], planner_q5[start:], planner_q95[start:], color=GetColor(planner), alpha=data["info"]["alpha_percentile"])
      else:
        planner_point = data[planner]["point"]
        time_errors, cost_errors = get_errors(planner_point)
        plt.errorbar(planner_point["time"][0], planner_point["cost"][0], cost_errors, time_errors, c=GetColor(planner), marker=GetMarker(planner), ms=10, lw=0.5)

    ax.grid(True, which="both", ls='--')
    ax.set_xlabel("run time [s]")
    ax.set_ylabel("solution cost")

def plot(json_filepath):
    with open(json_filepath, 'r') as jsonfile:
        data = json.load(jsonfile)

    # plt.style.use('../../test.mplstyle')
    fig, axs = plt.subplots(2, 1, sharex='col')
    plot_success(axs[0], data)
    plot_optimization(axs[1], data)

    axs[0].legend(loc='upper left', title='Planner')
    plt.show()
    plt.savefig(json_filepath+'.pdf', format='pdf', dpi=300, bbox_inches='tight')

def plot_database(database_filepath, info):
    json_filepath = os.path.splitext(database_filepath)[0]+'.json'

    data = {}
    data["info"] = info

    PrintInfo(database_filepath, data)

    with open(json_filepath, 'w') as jsonfile:
        json.dump(data, jsonfile, indent=4)

    plot(json_filepath)

if __name__ == '__main__':
    database_filepath = 'data/example.db'
    plot_database(database_filepath, info)

