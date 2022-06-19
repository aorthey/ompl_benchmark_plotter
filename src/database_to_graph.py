#!/usr/bin/python3
import sys
import json
import os
import sqlite3
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams
import argparse

from src.database_info import *
from src.plot_style import *

font_path = "config/cmr10.ttf"

fe = font_manager.FontEntry(
    fname=font_path,
    name='cmr10')
font_manager.fontManager.ttflist.insert(0, fe)
plt.rcParams['font.family'] = fe.name
plt.rcParams['mathtext.fontset']='cm'
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42

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

def get_json_from_database(cur, data, config):
  verbosity = config["verbosity"]
  ignore_non_optimal_planner = config["ignore_non_optimal_planner"]

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
  ### Verify that all experiment names match
  ############################################################
  # if not assert_equivalent_experiment_names(cur):
  #   print(get_experiment_names_from_database(cur))
  #   print("Error: All experiment names in database have to match to plot \
  #   optimality graph.")
  #   sys.exit(0)

  ############################################################
  ### Print Average Success per Planner over Time
  ############################################################
  if verbosity > 1:
    print(80*"-")
    print("-- Runs per planner ")
    print(80*"-")

  times = create_time_space(data)

  planners = cur.execute("SELECT id, name FROM {}".format('plannerConfigs')).fetchall()
  if ignore_non_optimal_planner:
    planners = remove_non_optimal_planner(planners)

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
  max_cost = data["info"]["max_cost"]
  ci_left = data["info"]["ci_left"]
  ci_right = data["info"]["ci_right"]
  if has_best_cost(cur):
    times = np.logspace(np.log10(min_time), np.log10(max_time), data["info"]["resolution"])

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
        success = get_count_success(cur, len(runs), runids, times)
        print("Planner {} success {} (runs {})".format(planner_name, success.tolist(), len(runs)))
        print("Planner {} median {} (runs {})".format(planner_name, results[1].tolist(), len(runs)))
        data[planner_name]["success"] = success.tolist()
      else:
        point_data = get_best_cost_from_runs(cur, planner_id, ci_left, ci_right)
        if point_data is None:
            point_data = max_point(max_time, max_cost)
        data[planner_name]["point"] = point_data
  else:
    if verbosity > 0:
      print("WARNING: No best_cost entry in database file. Using solution_length instead.")
    for planner in planners:
      planner_id = planner[0]
      planner_name = planner[1]
      data[planner_name]["optimization_success"] = False

      point_data = get_best_cost_from_runs(cur, planner_id, ci_left, ci_right)
      if point_data is None:
          point_data = max_point(max_time, max_cost)
      data[planner_name]["point"] = point_data


def get_best_cost_from_runs(cur, planner_id, ci_left, ci_right):
    return None
    # pair = np.array(cur.execute("SELECT time, solution_length FROM {0} WHERE plannerid={1} AND status=6".format('runs', planner_id)).fetchall())
    # if pair.size == 0:
    #     return None
    # split = np.split(pair, 2, axis=1)
    # times = split[0]
    # costs = split[1]
    # return calculate_points(times, costs, ci_left, ci_right)

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
    fontsize = data["info"]["fontsize"]

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
          linestyle=get_line_style(data, planner),
          linewidth=data["info"]["linewidth"], label=get_label(planner))

    ax.grid(True, which="both", ls='--')
    ylabel = data['info']['ylabel_success']
    ax.set_ylabel(ylabel, fontsize=fontsize)

def plot_optimization(ax, data, config):

    min_time = data["info"]["min_time"]["optimization"]
    max_time = data["info"]["max_time"]["optimization"]
    resolution = data["info"]["resolution"]
    times = np.logspace(np.log10(min_time), np.log10(max_time), resolution)

    max_cost = get_maxcost_from_json_or_config(data, config, times)
    min_cost = get_mincost_from_json_or_config(data, config, times, max_cost)

    fontsize = data["info"]["fontsize"]

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
          planner), linewidth=data["info"]["linewidth"], label=get_label(planner))
        ax.fill_between(times[start:], planner_q5[start:], planner_q95[start:],
            color=get_color(data, planner), alpha=data["info"]["alpha_percentile"])
      else:
        planner_point = data[planner]["point"]
        time_errors, cost_errors = get_errors(planner_point)
        plt.errorbar(planner_point["time"][0], planner_point["cost"][0],
            cost_errors, time_errors, c=get_color(data, planner),
            marker=get_marker_style(data, planner), ms=10, lw=0.5)

    ax.grid(True, which="both", ls='--')
    ylabel = data['info']['ylabel_optimization']
    xlabel = data['info']['xlabel']
    ax.set_xlabel(xlabel, fontsize=fontsize)
    ax.set_ylabel(ylabel, fontsize=fontsize)

def json_to_graph(json_filepath, pdf_filepath, config):
    with open(json_filepath, 'r') as jsonfile:
        data = json.load(jsonfile)

    fig, axs = plt.subplots(2, 1, sharex='col', figsize=(16,10))

    plot_success(axs[0], data)
    plot_optimization(axs[1], data, config)

    fontsize = data['info']['fontsize']
    label_fontsize = data['info']['label_fontsize']
    experiment_name = get_experiment_label(data["info"]["experiment"])

    if 'title_name' in config:
      axs[0].set_title(config['title_name'], fontsize=fontsize)
    else:
      axs[0].set_title(experiment_name, fontsize=fontsize)

    legend_title_name = 'Planner'
    if not config['legend_none']:
      if config['legend_separate_file']:
        figl, axl = plt.subplots()
        label_params = axs[0].get_legend_handles_labels() 
        legend = axl.legend(*label_params, loc="center", frameon=True, ncol=4, fontsize=fontsize)
        for obj in legend.legendHandles:
          obj.set_linewidth(data["info"]["legend_linewidth"])
        axl.axis('off')
        legend_filepath = change_filename_extension(json_filepath, '_legend.pdf')
        figl.savefig(legend_filepath, bbox_extra_artists=(legend,), bbox_inches='tight')
        plt.close(figl)

      elif config['legend_below_figure']:
        label_params = axs[0].get_legend_handles_labels() 
        legend = axs[1].legend(*label_params, loc='upper center', bbox_to_anchor=(0.5, -0.3),
                      fancybox=True, ncol=4, fontsize=fontsize)
        for obj in legend.legendHandles:
          obj.set_linewidth(data["info"]["legend_linewidth"])
        plt.setp(legend.get_title(),fontsize=label_fontsize)
      else:
        legend = axs[0].legend(loc='upper left', title=legend_title_name, fontsize=label_fontsize)
        for obj in legend.legendHandles:
          obj.set_linewidth(data["info"]["legend_linewidth"])
        plt.setp(legend.get_title(),fontsize=label_fontsize)

    axs[0].tick_params(labelsize=label_fontsize)
    axs[1].tick_params(labelsize=label_fontsize)

    fig = plt.gcf()
    if config['legend_separate_file'] or config['legend_none']:
      plt.savefig(pdf_filepath, format='pdf', dpi=300, bbox_inches='tight')
    else:
      plt.savefig(pdf_filepath, format='pdf', dpi=300, bbox_inches='tight', bbox_extra_artists=(legend,))

    if config['verbosity'] > 0:
      print("Wrote pdf with dpi %d to file %s" %(fig.dpi,pdf_filepath))
    if config['show']:
      os.system('xdg-open %s' % pdf_filepath)


def plot_graph_from_databases(database_filepaths, config):
    ############################################################
    ### Create data structure from database file
    ############################################################
    data = {}
    data["info"] = load_config()
    if config['max_cost'] > 0:
      data["info"]['max_cost'] = config['max_cost']
    if config['min_cost'] > 0:
      data["info"]['min_cost'] = config['min_cost']
    if config['fontsize'] > 0:
      data["info"]['fontsize'] = config['fontsize']
    if config['label_fontsize'] > 0:
      data["info"]['label_fontsize'] = config['label_fontsize']

    experiment_names = []
    experiment_times = []
    for database_filepath in database_filepaths:
      if not os.path.isfile(database_filepath):
        print("WARN: {} is not a file".format(database_filepath))
        continue
      extension = os.path.splitext(database_filepath)[1]
      if not (extension == '.db'):
        print("WARN: {} is not a db file".format(database_filepath))
        continue
      con = sqlite3.connect(database_filepath)
      cursor = con.cursor()

      get_maxtime_from_database_or_config(cursor, config, data)
      get_mintime_from_database_or_config(cursor, config, data)

      get_json_from_database(cursor, data, config)
      experiment_names.append(get_experiment_names_from_database(cursor))

    experiment_names = [item for sublist in experiment_names for item in sublist]
    experiment_names = list(set(experiment_names))

    data["info"]["experiment"] = get_experiment_name_from_array(experiment_names)

    ############################################################
    ### Verify that all experiment names match
    ############################################################

    if len(experiment_names) > 1:
      print(80*'#')
      print("WARN: Mismatching experiment names in database: {}".format(experiment_names))
      print("EXPECTED: Same name. Proceed with caution.".format(experiment_names))
      print(80*'#')

    if len(experiment_names) < 1 :
      print(80*'#')
      print("ERROR: Could not load experiments.")
      print(80*'#')
      sys.exit(1)

    if len(experiment_names) > 0 :
      data["info"]["experiment"] = get_experiment_name_from_array(experiment_names)

    ############################################################
    ### Create json file from data structure
    ############################################################
    json_filepath = get_json_filepath_from_databases(database_filepaths)
    with open(json_filepath, 'w') as jsonfile:
        json.dump(data, jsonfile, indent=4)

    ############################################################
    ### Plot json file to pdf
    ############################################################

    if config['output_file']:
      name = config['output_file']
      pdf_filepath = get_filename_from_database_filepaths_and_name(database_filepaths, name)
    else:
      pdf_filepath = change_filename_extension(json_filepath, '.pdf')

    json_to_graph(json_filepath, pdf_filepath, config)

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
