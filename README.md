# ompl_benchmark_plotter

Take a database file from an OMPL benchmark and generate graphs and tables.

## Functionality 1: Optimality Graphs

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
```
sudo apt-get install texlive-latex-extra
```

# TODO
- [ ] Table benchmark-to-benchmark improvement script
- [ ] Deterministic way to automatically pick colors

