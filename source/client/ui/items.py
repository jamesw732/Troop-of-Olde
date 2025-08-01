from ursina import *
from pathlib import Path

from .base import *
from ... import *


class ItemFrame(Entity):
    """A rectangular grid storing items."""
    def __init__(self, grid_size, container, slot_labels=[],
                 start_dragging=lambda x, y: None,**kwargs):
        self.grid_size = grid_size
        self.container = container
        # pad the slot labels with empty strings
        self.slot_labels = slot_labels + ([""] * (len(container) - len(slot_labels)))
        self.start_dragging = start_dragging

        self.boxes = [None] * len(container)

        super().__init__(collider="box", origin=(-0.5, 0.5), model='quad', color=slot_color, **kwargs)
        box_spacing = 0
        box_w = 1 / (grid_size[0] + box_spacing * (grid_size[0] - 1))
        box_h = 1 / (grid_size[1] + box_spacing * (grid_size[1] - 1))

        box_scale = Vec3(box_w, box_h, 1)

        positions = [(i, -j, -1) for j in range(int(self.grid_size[1])) for i in range(int(self.grid_size[0]))]

        for i, pos in enumerate(positions):
            self.boxes[i] = ItemBox(text=self.slot_labels[i], slot=i, container=self.container,
                               parent=self, position=pos * ((1 + box_spacing) * box_scale),
                               scale=box_scale)

        grid(self, int(grid_size[1]), int(grid_size[0]), color=color.black)

    def on_click(self):
        hovered_slot = self.get_hovered_slot()
        dragging_box = self.boxes[hovered_slot]
        dragging_icon = dragging_box.icon
        self.start_dragging(dragging_icon, dragging_box)

    def get_hovered_slot(self):
        ui_mouse_pos = mouse.position * camera.ui.scale
        rel_mouse_pos = ui_mouse_pos - self.world_position
        slot_world_pos = Vec2(self.world_scale_x, self.world_scale_y) / self.grid_size
        slot = Vec2(rel_mouse_pos[0], rel_mouse_pos[1]) / slot_world_pos
        slot = (int(slot[0]), int(slot[1]))
        return slot[0] - slot[1] * int(self.grid_size[0])


class ItemBox(Entity):
    def __init__(self, *args, text="", slot=None, container=None,  **kwargs):
        super().__init__(*args, origin=(-.5, .5), **kwargs)
        self.label = Text(text=text, parent=self, origin=(0, 0), position=(0.5, -0.5, -1),
                          world_scale=(11, 11), color=window_fg_color)

        self.label_text = text
        self.container = container
        self.slot = slot
        self.icon = None

    def set_item_icon(self, icon):
        self.icon = icon
        if icon is None:
            self.label.text = self.label_text
        else:
            self.label.text = ""
            icon.parent = self
            icon.position = Vec3(0, 0, -1)


class ItemIcon(Entity):
    """UI Representation of an Item."""
    def __init__(self, item, *args, **kwargs):
        self.item = item
        texture = item.icon_name
        load_texture(texture, folder=Path(item_icons_dir))
        super().__init__(*args, origin=(-.5, .5), model='quad', texture=texture, **kwargs)
