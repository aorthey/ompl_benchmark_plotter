#!/usr/bin/env python3
from collections import defaultdict
import subprocess
import glob
import re
import sys
import argparse
import os
import sqlite3
import numpy as np
import json
from src.plot_style import *
from src.database_info import *

def tex_table_from_json_data(database_filepaths, data, config):

    if config['output_file']:
      name = config['output_file']
      tex_name = change_filename_extension(name, ".tex")
      pdf_name = change_filename_extension(name, ".pdf")
      tex_filepath = get_filename_from_database_filepaths_and_name(database_filepaths, tex_name)
      pdf_filepath = get_filename_from_database_filepaths_and_name(database_filepaths, pdf_name)
    else:
      tex_filepath = get_tex_from_database_filepaths(database_filepaths)
      pdf_filepath = get_pdf_from_database_filepaths(database_filepaths)

    ############################################################
    ## Map planner to experiments
    ############################################################
    planner_map = {}
    for (ctr, experiment) in enumerate(data['experiments']):
      for (ctr, planner) in enumerate(data['experiments'][experiment]):
        if not planner in planner_map:
          planner_map[planner] = []
        planner_map[planner].append(experiment)

    if config['reverse']:
      longest_name=get_longest_name_from_planners(planner_map)
    else:
      longest_name=get_longest_name_from_experiments(data['experiments'])

    f = open(tex_filepath, 'w')

    f.write("\\documentclass{article}\n")
    f.write("\\usepackage{tabularx}\n")
    f.write("\\usepackage{rotating}\n")
    f.write("\\usepackage{makecell}\n")
    f.write("\\usepackage{xcolor}\n")
    f.write("\\usepackage[text={174mm,258mm}, papersize={210mm,297mm}, columnsep=12pt, headsep=21pt, centering]{geometry}")
    f.write("\\begin{document}\n\n")

    f.write("\\newcolumntype{V}{>{\\centering\\arraybackslash}m{.033\\linewidth}}\n")
    f.write("\\newcolumntype{Z}{>{\\raggedleft\\arraybackslash}m{.01\\linewidth}}\n")
    f.write("\\newcolumntype{+}{!{\\vrule width 1.2pt}}\n")

    f.write("\\begin{table*}[t]\n")
    f.write("\\centering\n")
    f.write("\\renewcommand{\\cellrotangle}{90}\n")
    f.write("\\renewcommand\\theadfont{\\bfseries}\n")

    f.write("\\settowidth{\\rotheadsize}{\\theadfont ") 
    f.write(str(longest_name))
    f.write("}\n")

    f.write("\\footnotesize\\centering\n")
    f.write("\\renewcommand{\\arraystretch}{1.2}\n")
    f.write("\\setlength\\tabcolsep{3pt}\n")

    if config['reverse']:
      n_columns = len(planner_map)
    else:
      n_columns = len(data['experiments'])

    format_str = "|ZX+"
    for i in range(0,n_columns):
      format_str += "X|"

    s = "\\begin{tabularx}{\\linewidth}{"+format_str+"}"

    s += "\\hline\n"
    s += "& & \\multicolumn{"+str(n_columns)
    s += "}{>{\\centering}p{.8\\textwidth}|}{List of Scenarios}\\\\"
    s += "\\cline{3-"+str(2+n_columns)+"}\n"

    ############################################################
    ## Create X-axis
    ############################################################
    if config['reverse']:
      s += "\\multicolumn{2}{|>{\\centering}p{2.5cm}+}{\\rothead{Scenario}}\n"
    else:
      s += "\\multicolumn{2}{|>{\\centering}p{2.5cm}+}{\\rothead{Motion Planner}}\n"

    if config['reverse']:
      for (ctr, planner) in enumerate(planner_map):
        name = get_label(planner).replace("#","\#")
        s += " & \\rothead{%s} \n"%(name)
    else:
      for (ctr, experiment) in enumerate(data['experiments']):
        name = get_experiment_label(experiment)
        s += " & \\rothead{%s} \n"%(name)
    s += " \\\\ \\hline\n"
    f.write(s)

    if config['reverse']:
      for (ctr, experiment) in enumerate(data['experiments']):
        label = get_experiment_label(experiment).replace("_"," ")
        pstr = str(ctr+1) + " & \\mbox{" + str(label) + "} & "
        for (pctr, planner) in enumerate(planner_map):
          if experiment in planner_map[planner]:
            pstr += get_cell_entry(data, experiment, planner, config)
          else:
            pstr += "$-$"
          if pctr < len(planner_map) - 1:
            pstr += " & "
          else: 
            pstr += " \\\\ \n"
        f.write(pstr)
    else:
      for (ctr, planner) in enumerate(planner_map):
        label = get_label(planner).replace("#","\#")
        pstr = str(ctr+1) + " & \\mbox{" + str(label) + "} & "
        for (ctr, experiment) in enumerate(data['experiments']):
          if experiment in planner_map[planner]:
            pstr += get_cell_entry(data, experiment, planner, config)
          else:
            pstr += "$-$"

          if ctr < len(data['experiments']) - 1:
            pstr += " & "
          else: 
            pstr += " \\\\ \n"
        f.write(pstr)

    f.write("\\hline\n")
    f.write("\\end{tabularx}\n")

    f.write("\\caption{Runtime (s) of %d runs with %s planning algorithms on %s scenarios \
        with cut-off time limit of %.2fs. \
    Entry '$-$' means that planner does not support this planning scenario.}\n"
    %(data['info']['run_count'], len(planner_map), len(data['experiments']), data['info']['timelimit']))

    f.write("\\end{table*}\n")
    f.write("\\end{document}\n")
    f.close()

    if config['verbosity'] > 1:
      os.system("pdflatex -output-directory %s %s" % (os.path.dirname(tex_filepath), tex_filepath))
      print(80*"#")
      print("Wrote tex file to %s" % tex_filepath)
      print(80*"#")
    else:
      os.system("pdflatex -output-directory %s %s > /dev/null 2>&1" % (os.path.dirname(tex_filepath), tex_filepath))

    ## Remove temporary/auxiliary files
    aux_file = os.path.splitext(tex_filepath)[0] + '.aux'
    log_file = os.path.splitext(tex_filepath)[0] + '.log'
    os.system("rm -rf %s" % (aux_file))
    os.system("rm -rf %s" % (log_file))

    if config['verbosity'] > 0:
      print("Created pdf file {}".format(pdf_filepath))
    if config['show']:
      os.system("xdg-open %s" % pdf_filepath)

def create_runtime_table_from_databases(database_filepaths, config):
    data = {}
    data["info"] = load_config()
    data["info"]["timelimit"] = 0
    data["info"]["run_count"] = 0
    data["experiments"] = {}

    for database_filepath in database_filepaths:
      con = sqlite3.connect(database_filepath)
      cursor = con.cursor()
      if config['verbosity'] > 1:
        print_metadata_from_database(cursor)
      if config['verbosity'] > 2:
        get_run_results_from_database(cursor)

      experiments = cursor.execute("SELECT id, name FROM {}".format('experiments')).fetchall()
      for experiment in experiments:
        experiment_name = experiment[1]
        experiment_id = experiment[0]
        timelimit = get_time_limit_for_experiment(cursor, experiment_id)
        data["info"]["timelimit"] = timelimit
        timespace = create_time_space_linear(data)
        planners = cursor.execute("SELECT id, name FROM {}".format('plannerConfigs')).fetchall()
        planner_data = {}
        best_time = float("inf")
        best_planner = ""

        for planner in planners:
          planner_id = planner[0]
          planner_name = planner[1]

          run_count = cursor.execute("SELECT COUNT(*) FROM {} WHERE plannerid={} AND experimentid={}".format('runs', planner_id, experiment_id)).fetchall()[0][0]

          times_per_run = cursor.execute("SELECT time FROM {} WHERE plannerid={} AND experimentid={}".format('runs', planner_id, experiment_id)).fetchall()
          times = np.array(times_per_run)
          if is_planner_optimal(planner_name):
            getids = cursor.execute("SELECT id FROM {} WHERE plannerid={}".format('runs',planner_id)).fetchall()
            runs = np.array(getids).flatten()
            runids = ','.join(str(run) for run in runs)
            success = get_count_success(cursor, len(runs), runids, timespace)
            times = get_times_from_success_over_time(success, timespace)

          solved_per_run = cursor.execute("SELECT solved FROM {} WHERE plannerid={} AND experimentid={}".format('runs', planner_id, experiment_id)).fetchall()

          success_percentage = np.sum(np.array(solved_per_run).flatten())/run_count
          time_mean = np.mean(times)
          planner_data[planner_name] = { 'time_mean' : time_mean,
              'time_variance' : np.std(times), 'success' : success_percentage,
              'time_limit' : timelimit,  'best_planner' : False, 'number_runs' : run_count}
          if timelimit > data['info']['timelimit']:
            data['info']['timelimit'] = timelimit
          if time_mean < best_time:
            best_time = time_mean
            best_planner = planner_name

        if best_time < float("inf"):
          planner_data[best_planner]['best_planner'] = True

        if config['ignore_ending_name']:
          experiment_name = experiment_name.rsplit('_', 1)[0]

        if not experiment_name in data['experiments']:
          data['experiments'][experiment_name] = planner_data
        else:
          planner_data = combine_planner_data(data['experiments'][experiment_name], planner_data)
          data['experiments'][experiment_name] = planner_data

    if len(database_filepaths) > 0:
      tex_table_from_json_data(database_filepaths, data, config)

