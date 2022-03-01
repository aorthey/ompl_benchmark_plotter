
def get_marker_style(data, planner_name):
  return data["info"]["markerstyle"]

def get_line_style(data, planner_name):
  return data["info"]["linestyle"]

def get_label(planner_name):
  name = planner_name.lstrip("geometric_")
  name = name.replace("Star","*")
  name = name.replace("star","*")
  name = name.replace("kBIT","BIT")
  return name

def get_experiment_label(experiment_name):
  name = experiment_name.replace("_"," ")
  name = name.title()
  return name

def get_color(data, planner_name):
  name = get_label(planner_name)
  colors = data["info"]["colors"]
  if name in colors:
    color = data["info"]["colors"][name]
  else:
    color = data["info"]["colors"]["default"]
  return color

