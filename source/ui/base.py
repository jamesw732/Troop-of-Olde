from ursina import *
import os

class UI:
    def __init__(self):
        self.bars = None
        self.playerwindow = None
        self.gamewindow = None

ui = UI()

# COLORS:
header_color = color.hex("8a6240")
active_button_color = color.hex("68401e")
window_bg_color = color.hex("4c6444")
window_fg_color = color.hex("666666")
text_color = color.hex("caffd7")
slot_color=color.hex("aaaaaa")

icons_dir = os.path.join(os.path.dirname(__file__), "..",
                         "..", "data", "item_icons")

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


def set_transparency(entity, alpha, ignore_key=lambda c: False):
    # Sets transparency of entity and all children of entity
    entity.alpha = alpha
    for child in entity.children:
        if not ignore_key(child):
            set_transparency(child, alpha, ignore_key=ignore_key)


def get_ui_parents(entities):
    """Recursively finds all parents of UI element until camera.ui is found, in reverse order
    entities: singleton list of one UI element"""
    next_parent = entities[0].parent
    if next_parent == camera.ui:
        # Don't return the last one
        return entities[:-1]
    return get_ui_parents([next_parent] + entities)

def get_global_y(y, entity):
    """Recursively finds the global position of a UI element

    y: a position in local space, relative to entity
    entity: an entity in UI space"""
    next_parent = entity.parent
    if next_parent is camera.ui:
        return y
    next_y = y * next_parent.scale_y + next_parent.y
    return get_global_y(next_y, next_parent)

def get_local_y(y, entities):
    """Iteratively finds the local position of a UI element given
    parents to follow

    y: a position in global space, relative to camera.ui
    entities: string of UI parents, likely returned by get_ui_parents"""
    for entity in entities:
        y = (y - entity.y) / entity.scale_y
    return y