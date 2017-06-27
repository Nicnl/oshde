
colors = [
    '\033[31m', # Red
    '\033[32m', # Green
    '\033[33m', # Yellow
    '\033[34m', # Blue
    '\033[35m', # Magenta
    '\033[36m', # Cyan
    '\033[90m', # Gray
]

reset = '\033[0m'

assign_counter = 0

def assign_color():
    global assign_counter

    assigned_color = colors[assign_counter]

    assign_counter += 1
    assign_counter %= len(colors)

    return assigned_color
