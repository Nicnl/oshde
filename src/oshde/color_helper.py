
colors = [
    '\033[91m', # Red
    '\033[92m', # Green
    '\033[93m', # Yellow
    '\033[94m', # Blue
    '\033[95m', # Magenta
    '\033[96m', # Cyan
    '\033[37m', # Gray
]

reset = '\033[0m'

assign_counter = 0

def assign_color():
    global assign_counter

    assigned_color = colors[assign_counter]

    assign_counter += 1
    assign_counter %= len(colors)

    return assigned_color
