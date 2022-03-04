# ompl_benchmark_plotter

This is an easy-to-use script to quickly generate graphs and tables from benchmark database file(s)
generated in the [Open Motion Planning Library
(OMPL)](https://github.com/ompl/ompl).


## Functionality 1: Optimality Graphs

Input: Any number of database files. They all should have a single environment. 
```
  ./ompl_benchmark_plotter.py examples/example.db -s
```

![Optimality Graph](examples/example.png)

### Options

* **-s**, **--show**
  Show output as pdf (requires xdg-open).
* **-t {0,1}**, **--type {0,1}**
  Select output format (0: plot optimality graphs, 1:
  create latex table of average runtimes).
* **-v {0,1,2,3}**, **--verbose {0,1,2,3}**
  Select verbosity level. Default: 1.
* **--quiet**
  Do not show any output. Invalidates any verbose values.

### Graph Options
* **--max-cost** _MAX-COST_
  Specify upper bound on cost display.
* **--max-time** _MAX-TIME_
  Specify upper bound on time display.
* **--min-time** _MIN-TIME_
  Specify lower bound on time display.
* **--fontsize** _FONTSIZE_
  Fontsize of title and descriptions.
* **--label-fontsize** _LABEL-FONTSIZE_
  Fontsize of tick labels.
* **--ignore-non-optimal-planner**
  Do not plot non-optimal planner.
* **--legend-separate-file**
  Print legend as separate file.
* **--legend-below-figure**
  Print legend below graph.
* **--legend-none**
  Do not print legend.

## Functionality 2: Average Runtime Table

```
  ./ompl_benchmark_plotter.py examples/example.db -t 1 -s
```

# Dependencies

To generate the tables, you need pdflatex and tex packages installed.

```
sudo apt-get install texlive-latex-extra
```

# TODO
- [ ] Table benchmark-to-benchmark improvement script
- [ ] Deterministic way to automatically pick colors

# Acknowledgements

[@gammell](https://github.com/gammell): This repository has been created as a tool to easily generate graphs similar to the
ones which [Jonathan Gammell](https://robotic-esp.com/people/gammell/) has used throughout his work (Check out his
amazing work on [asymptotically-optimal motion planning](https://robotic-esp.com/code/bitstar/).)

[@frangrothe](https://github.com/frangrothe): This library is also based upon earlier work by [Francesco Grothe](https://github.com/frangrothe),
who used optimality graphs extensively for his cool work on time-based motion
planning (Check it out here: https://github.com/frangrothe/bt-motion-planning).

[@servetb](https://github.com/servetb) and [@JayKamat99](https://github.com/JayKamat99): For feedback on earlier versions, and advice on improvements.
