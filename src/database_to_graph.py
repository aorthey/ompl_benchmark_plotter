#!/usr/bin/python3
import sys
import json
import os
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import argparse

from src.database_info import *
from src.plot_style import *

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

def get_json_from_database(cur, data, verbosity):
  if verbosity > 1:
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

  if verbosity > 2:
    get_run_results_from_database(cur)

  ############################################################
  ### Print Average Success per Planner over Time
  ############################################################
  if verbosity > 1:
    print(80*"-")
    print("-- Runs per planner ")
    print(80*"-")

  times = np.logspace(np.log10(data["info"]["min_time"]["success"]), np.log10(data["info"]["max_time"]["success"]),
                      data["info"]["resolution"])

  planners = cur.execute("SELECT id, name FROM {}".format('plannerConfigs')).fetchall()
  for planner in planners:
    planner_id = planner[0]
    planner_name = planner[1]
    number_runs = cur.execute("SELECT COUNT(*) FROM {} WHERE plannerid={}".format('runs', planner_id)).fetchall()[0][0]

    percentages = np.empty(len(times))
    for i in range(len(times)):
        percentage = cur.execute(
            "SELECT COUNT(*) FROM {0} WHERE plannerid={2} AND time < {1}".format('runs', times[i], planner_id)).fetchall()
        percentages[i] = (percentage[0][0] / number_runs) * 100
    data[planner_name] = {
        "success": percentages.tolist()
        }
    if verbosity > 1:
      print("Planner {} (id {}) has {} runs.".format(planner_name, planner_id, number_runs))

  ############################################################
  ### Get Cost per Planner over Time
  ############################################################
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
      point_data = get_best_cost_from_runs(cur, planner_id, ci_left, ci_right)
      if point_data is None:
          point_data = max_point(max_time, max_cost)
      data[planner_name]["point"] = point_data


def get_start_index(medians, times, max_cost):
    for i in range(len(times)):
        if medians[i] < max_cost:
            return i
    return len(times)

def get_best_cost_from_runs(cur, planner_id, ci_left, ci_right):
    pair = np.array(cur.execute("SELECT time, solution_length FROM {0} WHERE plannerid={1} AND status=6".format('runs', planner_id)).fetchall())
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

      success_over_time = data[planner]["success"]
      ax.plot(times, success_over_time, color=get_color(data, planner),
          linestyle=get_line_style(data, planner), label=get_label(planner))

    ax.grid(True, which="both", ls='--')
    ax.set_ylabel("success [%]")

def plot_optimization(ax, data):

    min_time = data["info"]["min_time"]["optimization"]
    max_time = data["info"]["max_time"]["optimization"]
    resolution = data["info"]["resolution"]
    times = np.logspace(np.log10(min_time), np.log10(max_time), resolution)
    max_cost = data["info"]["max_cost"]
    min_cost = data["info"]["min_cost"]

    ax.set_xscale('log')
    ax.set_yscale('linear')
    ax.set_xlim(min_time, max_time)
    ax.set_ylim(min_cost, max_cost)

    for planner in data:
      if planner == "info":
        continue

      planner_optimization_success = data[planner]["optimization_success"]
      if planner_optimization_success:
        planner_median = data[planner]["median"]
        planner_q5 = data[planner]["quantile5"]
        planner_q95 = data[planner]["quantile95"]

        start = get_start_index(planner_median, times, max_cost)
        ax.plot(times[start:], planner_median[start:], color=get_color(data,
          planner), label=get_label(planner))
        ax.fill_between(times[start:], planner_q5[start:], planner_q95[start:],
            color=get_color(data, planner), alpha=data["info"]["alpha_percentile"])
      else:
        planner_point = data[planner]["point"]
        time_errors, cost_errors = get_errors(planner_point)
        plt.errorbar(planner_point["time"][0], planner_point["cost"][0],
            cost_errors, time_errors, c=get_color(data, planner),
            marker=get_marker_style(data, planner), ms=10, lw=0.5)

    ax.grid(True, which="both", ls='--')
    ax.set_xlabel("run time [s]")
    ax.set_ylabel("solution cost")

def json_to_graph(json_filepath, verbosity, show):
    with open(json_filepath, 'r') as jsonfile:
        data = json.load(jsonfile)

    fig, axs = plt.subplots(2, 1, sharex='col', figsize=(16,10))
    plot_success(axs[0], data)
    plot_optimization(axs[1], data)

    experiment_name = get_experiment_label(data["info"]["experiment"])
    axs[0].title.set_text(experiment_name)
    axs[0].legend(loc='upper left', title='Planner')
    pdf_filepath = json_filepath+'.pdf'
    # plt.savefig(pdf_filepath, format='pdf', dpi=300, bbox_inches='tight')
    fig = plt.gcf()
    plt.savefig(pdf_filepath, format='pdf', dpi=300, bbox_inches='tight')
    if verbosity > 0:
      print("Wrote pdf with dpi %d to file %s" %(fig.dpi,pdf_filepath))
    if show:
      plt.show()


def plot_graph_from_database(database_filepath, verbosity=0, show=False, max_cost=-1, max_time=-1, min_time=-1):
    ############################################################
    ### Create data structure from database file
    ############################################################
    con = sqlite3.connect(database_filepath)
    cursor = con.cursor()
    data = {}
    data["info"] = load_config()
    if max_cost > 0:
      data["info"]['max_cost'] = max_cost
    if max_time > 0:
      data["info"]['max_time']['success'] = max_time
      data["info"]['max_time']['optimization'] = max_time
    if min_time > 0:
      data["info"]['min_time']['success'] = min_time
      data["info"]['min_time']['optimization'] = min_time

    get_json_from_database(cursor, data, verbosity)
    experiment_names = get_experiment_names_from_database(cursor)
    if len(experiment_names) > 0 :
      data["info"]["experiment"] = experiment_names[0]

    ############################################################
    ### Create json file from data structure
    ############################################################
    # json_filepath = os.path.splitext(database_filepath)[0]+'.json'
    json_filepath = get_json_filepath_from_database(database_filepath)
    with open(json_filepath, 'w') as jsonfile:
        json.dump(data, jsonfile, indent=4)

    ############################################################
    ### Plot json file
    ############################################################
    json_to_graph(json_filepath, verbosity, show)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plotting of Benchmark Files (especially for asymptotically-optimal planner).')
    parser.add_argument('database_file', type=str, nargs='?', help='Database (.db) file')
    args = parser.parse_args()

    fname = args.database_file
    if fname is None:
      fname="data/example.db"

    if os.path.isfile(fname):
      plot_graph_from_database(fname)
    else:
      print("Error: {} is not a file.".format(fname))
