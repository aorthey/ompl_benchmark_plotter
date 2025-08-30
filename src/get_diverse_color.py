import colorsys
import itertools

# Define a good color palette for graphs
# These colors are chosen to be distinct and visually appealing for data representation
graph_colors = [
    '#d62728',  # brick red
    '#1f77b4',  # muted blue
    '#2ca02c',  # cooked asparagus green
    '#9467bd',  # muted purple
    '#8c564b',  # chestnut brown
    '#ff7f0e',  # safety orange
    '#e377c2',  # raspberry yogurt pink
    '#7f7f7f',  # middle gray
    '#bcbd22',  # curry yellow-green
    '#17becf'   # blue-teal
]

# Create a global color map to store the color for each planner
global_color_map = {}

# Use itertools.cycle to create an infinite loop through these colors
color_cycler = itertools.cycle(graph_colors)

def get_diverse_color(planner_name):
    global global_color_map

    if planner_name in global_color_map:
        return global_color_map[planner_name]

    hex_color = next(color_cycler)
    global_color_map[planner_name] = hex_color
    return hex_color

def rgba_to_hex(rgba):
    r, g, b, _ = [int(x * 255) for x in rgba]
    return f"#{r:02x}{g:02x}{b:02x}"
