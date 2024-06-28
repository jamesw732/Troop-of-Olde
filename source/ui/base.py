from ursina import *

# COLORS:
header_color = color.hex("8a6240")
active_button_color = color.hex("68401e")
window_bg_color = color.hex("4c6444")
window_fg_color = color.hex("666666")



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

def get_hovered(entity):
    # Returns whether this entity is hovered, or whether any of its children are hovered
    if entity.hovered:
        return True
    if not entity.children:
        return False
    return any((get_hovered(child) for child in entity.children if child.collider))

def set_transparency(entity, alpha, ignore_key=lambda c: False):
    # Sets transparency of entity and all children of entity
    entity.alpha = alpha
    for child in entity.children:
        if not ignore_key(child):
            set_transparency(child, alpha, ignore_key=ignore_key)