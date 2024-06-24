from ursina import *

# COLORS:
header_color = color.hex("8a6240")
window_bg_color = color.hex("4c6444")



def grid(entity, num_rows, num_cols, margin_x=0, margin_y=0):
    """Helper function for drawing a grid over a UI element
    Margins are numbers from 0 to 1."""
    for row in range(num_rows + 1):
        vertices = [(margin_x,
                     -margin_y - (row / num_rows) * (1 - 2 * margin_y),
                     0),

                    (1 - margin_x,
                     -margin_y - (row / num_rows) * (1 - 2 * margin_y),
                    0)]
        Entity(parent=entity, model=Mesh(vertices=vertices, mode="line"), color=color.white)
    for col in range(num_cols + 1):
        vertices = [(margin_x + (col / num_cols) * (1 - 2 * margin_x),
                     -margin_y,
                     0),

                     (margin_x + col / num_cols * (1 - 2 * margin_x),
                      -1 + margin_y,
                      0)]
        Entity(parent=entity, model=Mesh(vertices=vertices, mode="line"), color=color.white)