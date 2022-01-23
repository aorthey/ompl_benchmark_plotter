
def get_marker_style(data, planner_name):
  return data["info"]["markerstyle"]

def get_line_style(data, planner_name):
  return data["info"]["linestyle"]

def get_label(planner_name):
  name = planner_name.lstrip("geometric_")
  return name

def get_experiment_label(experiment_name):
  name = experiment_name.replace("_"," ")
  # name = name.rstrip("_benchmark")
  name = name.title()
  return name


def get_color(data, planner_name):
  name = get_label(planner_name)
  color = data["info"]["colors"][name]
  if color is None:
    color = data["info"]["colors"]["default"]
  return color

