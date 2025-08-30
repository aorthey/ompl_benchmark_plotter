#!/usr/bin/env python3
import argparse
import os
import re
from src.database_to_graph import *

############################################################
## Setup argument parser
############################################################

def run_benchmark_plotter(input_arguments):
  parser = argparse.ArgumentParser(description='Plotting of OMPL Benchmark Files.')

  parser.add_argument('database_files', type=str, nargs='+', help='Database (.db) file(s)')
  parser.add_argument('-v','--verbose', type=int, choices=[0,1,2,3], default=1, help='Select verbosity level for stdout.')
  parser.add_argument('-q', '--quiet', action='store_const', const=True, help='Do not show any output. Invalidates any verbose values.')
  parser.add_argument('-s','--show', action='store_const', const=True, help='Show output as pdf (requires xdg-open).')
  parser.add_argument('-o','--output-file', type=str, help='Save as filename.')

  #### Options for optimality graph
  graph_group = parser.add_argument_group("Cost-success graph options")
  graph_group.add_argument('--max-cost', type=float, help='Specify upper bound on cost display.')
  graph_group.add_argument('--min-cost', type=float, help='Specify lower bound on cost display.')
  graph_group.add_argument('--max-time', type=float, help='Specify upper bound on time display.')
  graph_group.add_argument('--min-time', type=float, help='Specify lower bound on time display.')
  graph_group.add_argument('--linewidth', type=float, help='Linewidth of the output.')
  graph_group.add_argument('--fontsize', type=float, help='Fontsize of title and descriptions.')
  graph_group.add_argument('--label-fontsize', type=float, help='Fontsize of tick labels.')
  graph_group.add_argument('--only-success-graph', action='store_const', const=True, help='Plot only the success graph.')
  graph_group.add_argument('--ignore-non-optimal-planner', action='store_const', const=True, help='Do not plot non-optimal planner.')
  graph_group.add_argument('--ignore-planner', action='store', type=str, nargs='+', help='Exclude planners from graph (accepts multiple planner names)')
  graph_group.add_argument('--legend-separate-file', action='store_const', const=True, help='Print legend as separate file.')
  graph_group.add_argument('--legend-below-figure', action='store_const', const=True, help='Print legend below graph.')
  graph_group.add_argument('--legend-none', action='store_const', const=True, help='Do not print legend.')
  graph_group.add_argument('--remove-ylabel', action='store_const', const=True, help='Do not print label on y-axis.')
  graph_group.add_argument('--title-name', action='store', type=str, help='Set title name.')
  graph_group.add_argument('--no-title', action='store_const', const=True, help='Do not set a title for this graph')
  graph_group.add_argument('--planner-color', type=str, action='append', help='Specify custom colors for planners as PlannerName=(R,G,B,A), e.g., --planner-color Planner1=(0.7,0.1,0.7,1.0)')

  args = parser.parse_args(input_arguments)
  if args.quiet:
    args.verbose = 0

  ############################################################
  ## Parse custom planner colors
  ############################################################
  planner_colors = {}
  if args.planner_color:
    for color_spec in args.planner_color:
      match = re.match(r'(\w+)=\((\d*\.?\d+),(\d*\.?\d+),(\d*\.?\d+),(\d*\.?\d+)\)', color_spec)
      if match:
        planner_name = match.group(1)
        rgba = tuple(float(match.group(i)) for i in range(2, 6))
        if all(0 <= v <= 1 for v in rgba):
          planner_colors[planner_name] = rgba
        else:
          if args.verbose > 0:
            print(f"Error: RGBA values for {planner_name} must be between 0 and 1.")
          return 1
      else:
        if args.verbose > 0:
          print(f"Error: Invalid color format for {color_spec}. Expected PlannerName=(R,G,B,A).")
        return 1

  ############################################################
  ## Sanity checks
  ############################################################
  if args.show:
    from shutil import which
    if which("xdg-open") is None:
      print("Error: Cannot run with --show option if xdg-open is not installed.")
      return 1

  for fname in args.database_files:
    if fname is None or not os.path.isfile(fname):
      if args.verbose > 0:
        print("Error: {} is not a file.".format(fname))
        return 1

  ############################################################
  ## Run the chosen program
  ############################################################
  if args.verbose > 0:
    print("Create optimality graphs for {} files.".format(len(args.database_files)))

  plot_config = make_config(args)
  plot_config["planner_colors"] = planner_colors
  plot_graph_from_databases(args.database_files, plot_config)

  return 0

if __name__ == '__main__':
  import sys
  sys.exit(run_benchmark_plotter(sys.argv[1:]))
