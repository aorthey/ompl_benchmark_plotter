# ompl_benchmark_plotter

This is an easy-to-use script to quickly generate optimality graphs (as pdf) from benchmark database file(s) generated in the [Open Motion Planning Library (OMPL)](https://github.com/ompl/ompl).

## Generating optimality graphs

Input: Any number of database files. 
```
  ./ompl_benchmark_plotter.py examples/example.db -s
```

![Optimality Graph](examples/example.png)

### Options

* **-o**, **--output-file** _PDF-FILENAME_
  Specify output pdf filename 
* **-s**, **--show**
  Show output as pdf (requires xdg-open).
* **-v {0,1,2,3}**, **--verbose {0,1,2,3}**
  Select verbosity level. Default: 1.
* **--quiet**
  Do not show any output. Invalidates any verbose values.

### Graph Options

NOTE: default values can be found in ```config/default.json```

* **--max-cost** _MAX-COST_
  Specify upper bound on cost axis.
* **--min-cost** _MIN-COST_
  Specify lower bound on cost axis.
* **--max-time** _MAX-TIME_
  Specify upper bound on time axis.
* **--min-time** _MIN-TIME_
  Specify lower bound on time axis.
* **--fontsize** _FONTSIZE_
  Fontsize of title and descriptions.
* **--label-fontsize** _LABEL-FONTSIZE_
  Fontsize of tick labels.
* **--ignore-non-optimal-planner**
  Do not plot non-optimal planner.
* **--title-name** _TITLE-NAME_ 
  Set title name
* **--legend-separate-file**
  Print legend as separate file.
* **--legend-below-figure**
  Print legend below graph.
* **--legend-none**
  Do not print legend.

# Acknowledgements

[@gammell](https://github.com/gammell): This repository has been created as a tool to easily generate graphs similar to the
ones which [Jonathan Gammell](https://robotic-esp.com/people/gammell/) has used throughout his work (Check out his
work on [asymptotically-optimal motion planning](https://robotic-esp.com/code/bitstar/).)

[@frangrothe](https://github.com/frangrothe): This library is also based upon earlier work by [Francesco Grothe](https://github.com/frangrothe),
who used optimality graphs extensively for his work on time-based motion
planning (Check it out here: https://github.com/frangrothe/bt-motion-planning).

[@servetb](https://github.com/servetb) and [@JayKamat99](https://github.com/JayKamat99): For feedback on earlier versions, and advice on improvements.
