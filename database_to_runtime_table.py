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

def plot_table_from_data(database_filepath, data):
    tex_filepath = os.path.splitext(database_filepath)[0]+'.tex'
    pdf_filepath = os.path.splitext(database_filepath)[0]+'.pdf'

    #pdfName = '../../data/benchmarks/table.pdf'

    #d = defaultdict(dict)
    #planner_names_tmp = []
    #env_names_tmp = []

    #Nruns = 0
    #for f in fnames:
    #  benchmark = BenchmarkAnalytica(f)
    #  env = benchmark.benchmark_name
    #  env = env.replace("_"," ")
    #  print(f, env)
    #  if benchmark.runcount > Nruns:
    #    Nruns = benchmark.runcount
    #  env_names_tmp.append(env)
    #  for p in benchmark.planners:
    #    pname = p.name
    #    pname = pname.replace("#","\#")
    #    pname = re.sub('[Ss]tar', '*', pname)
    #    # pname = re.sub('CForest', 'CForest<RRT>', pname)

    #    planner_names_tmp.append(pname)
    #    d[env][pname] = p.AverageTime()

    ### unique list
    #planner_names = []
     
    #for p in planner_names_tmp:
    #  if p not in planner_names:
    #    planner_names.append(p) 

    #env_names = []
    #for e in env_names_tmp:
    #  if e not in env_names:
    #    env_names.append(e)
    #env_names = sorted(env_names)

    #Nplanner = len(planner_names)
    #Nenv = len(env_names)

    #####################################################
    ###### FIND OUT ENVIRONMENTS ########################
    #####################################################
    #dir_name = "../../data/experiments/21-Review/"
    #print(80*"X")
    #topics = defaultdict(dict)
    #for r1, d1, f1 in os.walk(dir_name):
    #  for d2 in d1:
    #    envs = []
    #    for root, tmp, files in os.walk(dir_name+d2):
    #      for f in files:
    #        env = os.path.splitext(f)[0]
    #        env = env.replace("_"," ")
    #        print(dir_name+d2, env)
    #        envs.append(env)
    #    tmp = d2.replace("_"," ")
    #    topics[tmp] = envs

    ## create tex


    f = open(tex_filepath, 'w')

    f.write("\\documentclass{article}\n")
    f.write("\\usepackage{tabularx}\n")
    f.write("\\usepackage{rotating}\n")
    f.write("\\usepackage{makecell}\n")
    f.write("\\usepackage[text={174mm,258mm}, papersize={210mm,297mm}, columnsep=12pt, headsep=21pt, centering]{geometry}")
    f.write("\\begin{document}\n\n")

    f.write("\\newcolumntype{V}{>{\\centering\\arraybackslash}m{.033\\linewidth}}\n")
    f.write("\\newcolumntype{W}{>{\\centering\\arraybackslash}m{.036\\linewidth}}\n")
    f.write("\\newcolumntype{Z}{>{\\raggedleft\\arraybackslash}m{.01\\linewidth}}\n")
    f.write("\\newcolumntype{Y}{>{\\centering\\arraybackslash}X}\n")
    f.write("\\newcolumntype{+}{!{\\vrule width 1.2pt}}\n")

    f.write("\\begin{table*}[t]\n")
    f.write("\\centering\n")
    f.write("\\renewcommand{\\cellrotangle}{90}\n")
    f.write("\\renewcommand\\theadfont{\\bfseries}\n")

    #TODO(replace name)
    f.write("\\settowidth{\\rotheadsize}{\\theadfont 37D Shadowhand ball}\n")

    f.write("\\footnotesize\\centering\n")
    f.write("\\renewcommand{\\arraystretch}{1.2}\n")
    f.write("\\setlength\\tabcolsep{3pt}\n")

    n = len(data['experiments'])

    #TODO(make list variable)

    format_str = "|ZX+"
    for i in range(0,n):
      format_str += "W|"

    s = "\\begin{tabularx}{\\linewidth}{"+format_str+"}"

    s += "\\hline\n"
    s += "& & \\multicolumn{"+str(n)+"}{Y+}{List of Scenarios} \\\\ \\cline{3-"+str(3+n)+"}\n"

    s += " & & \n"

    ############################################################
    ## Create X-axis
    ############################################################
    for (ctr, experiment) in enumerate(data['experiments']):
      name = get_experiment_label(experiment)
      s += "%s & %s "%(ctr, name)
      if ctr < len(data['experiments'])-1:
        s += " &\n" 
    s += "\\\\ \\cline{3-{1}}\n\n".format(3+n)

    s += "\\multicolumn{2}{|>{\\centering}p{2.5cm}+}{\\rothead{Motion Planner}}\n"
    for (ctr, experiment) in enumerate(data['experiments']):
      s += " %" #comment
      s += " %s\n"%(t) #comment
      s += " & \\rothead{%s} \n"%(p)
    s += " \\\\ \\hline\n"
    f.write(s)

    ############################################################
    ## Create Y-axis
    ############################################################
    for (ctr, experiment) in enumerate(data['experiments']):
      for (ctr, planner) in enumerate(data['experiments'][experiment]):
        pstr = str(ctr+1) + " & \\mbox{" + str(planner) + "} & \n"
        # for (ctrt,t) in enumerate(sorted(topics)):
        #   n = len(topics[t])
        #   if n > 0:
        #     for (ctrenv, env) in enumerate(topics[t]):
        #       if p in d[env]:
        #         s = d[env].get(p)
        #         # pstr += (" %.3f " % s)
        #         bestPlanner = min(d[env],key=d[env].get)
        #         if env.startswith('02D') and (s < 10.0):
        #           if p == bestPlanner:
        #             pstr += (" \\textbf{%.3f} " % s)
        #           else:
        #             pstr += (" %.3f " % s)
        #         else:
        #           if p == bestPlanner:
        #             pstr += (" \\textbf{%.2f} " % s)
        #           else:
        #             pstr += (" %.2f " % s)
        #       else:
        #         pstr += " - " 
        #       if ctrenv < len(topics[t])-1:
        #         pstr += " &" 
        #     if ctrt < len(topics)-1:
        #       pstr += " & % "
        #       pstr += ("%s\n"%t)
        #   else:
        #     pstr += " &&"
        #     if ctrt < len(topics)-1:
        #       pstr += "&" 
        #     pstr +=" % "
        #     pstr += ("%s\n"%t)

        pstr += " \\\\ \n"
        f.write(pstr)

    f.write("\\hline\n")
    f.write("\\end{tabularx}\n")


    f.write("\\caption{Runtime (s) of motion planner on N scenarios in each averaged over $2$ runs with cut-off time limit of $60$s. \
    Entry $-$ means that planner does not support this planning scenario.}\n")

    f.write("\\end{table*}\n")
    f.write("\\end{document}\n")
    f.close()

    os.system("pdflatex -output-directory %s %s" % (os.path.dirname(tex_filepath), tex_filepath))
    print("Wrote tex file to %s" % tex_filepath)
    os.system("apvlv %s" % pdf_filepath)

def get_data(database_filepath):
    ############################################################
    ### Create data structure from database file
    ############################################################
    con = sqlite3.connect(database_filepath)
    cursor = con.cursor()
    print_metadata_from_database(cursor)
    data = {}
    data["info"] = load_config()
    # get_average_runtime_from_database(cursor, data)

    experiments = cursor.execute("SELECT id, name FROM {}".format('experiments')).fetchall()
    experiment_data = {}
    for experiment in experiments:
        experiment_name = experiment[1]
        experiment_id = experiment[0]

        planners = cursor.execute("SELECT id, name FROM {}".format('plannerConfigs')).fetchall()
        planner_data = {}
        for planner in planners:
          planner_id = planner[0]
          planner_name = planner[1]

          run_count = cursor.execute("SELECT COUNT(*) FROM {} WHERE plannerid={} AND experimentid={}".format('runs', planner_id, experiment_id)).fetchall()[0][0]
          times_per_run = cursor.execute("SELECT time FROM {} WHERE plannerid={} AND experimentid={}".format('runs', planner_id, experiment_id)).fetchall()
          solved_per_run = cursor.execute("SELECT solved FROM {} WHERE plannerid={} AND experimentid={}".format('runs', planner_id, experiment_id)).fetchall()

          times = np.array(times_per_run)
          success_percentage = np.sum(np.array(solved_per_run).flatten())/run_count
          planner_data[planner_name] = { 'time_mean' : np.mean(times),
              'time_variance' : np.var(times), 'success' : success_percentage }

        experiment_data[experiment_name] = planner_data
    data['experiments'] = experiment_data
    print(data)
    plot_table_from_data(database_filepath, data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plotting of Benchmark Files (especially for asymptotically-optimal planner).')
    parser.add_argument('database_file', type=str, nargs='?', help='Database (.db) file')
    args = parser.parse_args()

    fname = args.database_file
    if fname is None:
      fname="data/example.db"

    if os.path.isfile(fname):
      get_data(fname)
    else:
      print("Error: {} is not a file.".format(fname))
