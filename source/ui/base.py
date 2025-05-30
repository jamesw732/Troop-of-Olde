from ursina import *
import os


# COLORS:
header_color = color.hex("8a6240")
active_button_color = color.hex("68401e")
window_bg_color = color.hex("4c6444")
window_fg_color = color.hex("666666")
text_color = color.hex("caffd7")
slot_color=color.hex("aaaaaa")

item_icons_dir = os.path.join(os.path.dirname(__file__), "..",
                         "..", "data", "item_icons")
effect_icons_dir = os.path.join(os.path.dirname(__file__), "..",
                         "..", "data", "effect_icons")

def grid(entity, num_rows, num_cols, margin_x=0, margin_y=0, color=color.white):
    """Helper function for drawing a grid over a UI element
    Margins are numbers from 0 to 1."""
    for row in range(num_rows + 1):
        vertices = [(margin_x,
                     -margin_y - (row / num_rows) * (1 - 2 * margin_y),
                     -10),

                    (1 - margin_x,
                     -margin_y - (row / num_rows) * (1 - 2 * margin_y),
                    -10)]
        Entity(parent=entity, model=Mesh(vertices=vertices, mode="line"), color=color)
    for col in range(num_cols + 1):
        vertices = [(margin_x + (col / num_cols) * (1 - 2 * margin_x),
                     -margin_y,
                     -10),

                     (margin_x + col / num_cols * (1 - 2 * margin_x),
                      -1 + margin_y,
                      -10)]
        Entity(parent=entity, model=Mesh(vertices=vertices, mode="line"), color=color)

