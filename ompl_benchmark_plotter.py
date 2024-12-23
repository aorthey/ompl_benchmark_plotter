#!/usr/bin/env python3
import argparse
import os
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
  graph_group.add_argument('--fontsize', type=float, help='Fontsize of title and descriptions.')
  graph_group.add_argument('--label-fontsize', type=float, help='Fontsize of tick labels.')
  graph_group.add_argument('--ignore-non-optimal-planner', action='store_const', const=True, help='Do not plot non-optimal planner.')
  graph_group.add_argument('--legend-separate-file', action='store_const', const=True, help='Print legend as separate file.')
  graph_group.add_argument('--legend-below-figure', action='store_const',
      const=True, help='Print legend below graph.')
  graph_group.add_argument('--legend-none', action='store_const',
      const=True, help='Do not print legend.')
  graph_group.add_argument('--title-name', action='store', type=str, help='Set title name.')

  args = parser.parse_args(input_arguments)
  if args.quiet:
    args.verbose = 0

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
  plot_graph_from_databases(args.database_files, plot_config)

  return 0

if __name__ == '__main__':
  sys.exit(run_benchmark_plotter(sys.argv[1:]))
