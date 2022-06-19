#!/usr/bin/env python3
import argparse
import os
from src.database_to_graph import *
from src.database_to_runtime_table import *

############################################################
## Setup argument parser
############################################################

def run_benchmark_plotter(input_arguments):
  parser = argparse.ArgumentParser(description='Plotting of OMPL Benchmark Files.')

  parser.add_argument('database_files', type=str, nargs='+', help='Database (.db) file(s)')
  parser.add_argument('-t','--type', type=int, choices=[0,1], default=0, help='Select output format (0: plot \
      optimality graphs, 1: create latex table of average runtimes).')
  parser.add_argument('-v','--verbose', type=int, choices=[0,1,2,3], default=1, help='Select verbosity level.')
  parser.add_argument('-q', '--quiet', action='store_const', const=True, help='Do not show any output. Invalidates any verbose values.')
  parser.add_argument('-s','--show', action='store_const', const=True, help='Show output as pdf (requires xdg-open).')
  parser.add_argument('-o','--output-file', type=str, help='Save as filename.')

  #### Options for optimality graph
  graph_group = parser.add_argument_group("optimality graph options")
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

  #### Options for runtime table
  table_group = parser.add_argument_group("table options")
  table_group.add_argument('--table-hide-variance', action='store_const', const=True, help='Do not show variance in runtime table.')
  table_group.add_argument('--reverse-table', action='store_const', const=True, \
      help='Reverse positions of planners and scenarios in table (default: \
      planners on y-axis, scenarios on x-axis).')
  table_group.add_argument('--ignore-ending-name', action='store_const', const=True, \
          help='In environment names, ignore anything beyond the last occurence of \
          "_", for example "Name_01" and "Name_02" are considered as "Name".')
  table_group.add_argument('--decimals', type=int, default=2, help='Select number \
      of decimals after point in table.')
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
  if args.type == 0:
    if args.verbose > 0:
      print("Create optimality graphs for {} files.".format(len(args.database_files)))

    max_cost = args.max_cost if args.max_cost else -1
    min_cost = args.min_cost if args.min_cost else -1
    max_time = args.max_time if args.max_time else -1
    min_time = args.min_time if args.min_time else -1
    fontsize = args.fontsize if args.fontsize else -1
    label_fontsize = args.label_fontsize if args.label_fontsize else -1
    plot_config = {
        'show': args.show,
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
    # title_name = args.title_name if args.title_name else -1
    if args.title_name:
      plot_config['title_name'] = args.title_name
    plot_graph_from_databases(args.database_files, plot_config)
    # for fname in args.database_files:
    #   plot_graph_from_database(fname, plot_config)

  elif args.type == 1:
    if args.verbose > 0:
      print("Create runtime table with {} files.".format(len(args.database_files)))
    table_config = {
        'show': args.show,
        'decimals': args.decimals,
        'output_file': args.output_file,
        'verbosity': args.verbose,
        'reverse': args.reverse_table,
        'hide_variance': args.table_hide_variance,
        'ignore_ending_name': args.ignore_ending_name
    }
    create_runtime_table_from_databases(args.database_files, table_config)
  else:
    return ("Error: type {} not recognized.", args.type)

  return 0

if __name__ == '__main__':
  sys.exit(run_benchmark_plotter(sys.argv[1:]))
