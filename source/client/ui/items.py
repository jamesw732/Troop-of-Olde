from ursina import *

from .base import *
from ... import *


inst_id_to_item_icon = {}


class ItemFrame(Entity):
    """A rectangular grid storing items."""
    def __init__(self, grid_size, container, slot_labels=[], **kwargs):
        self.grid_size = grid_size
        self.container = container
        # pad the slot labels with empty strings
        self.slot_labels = slot_labels + ([""] * (len(container) - len(slot_labels)))

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
            icon = self.make_item_icon(container[i], self.boxes[i])
            self.boxes[i].icon = icon
            if icon is not None:
                self.boxes[i].label.text = ""

        grid(self, int(grid_size[1]), int(grid_size[0]), color=color.black)

        self.dragging_icon = None
        self.dragging_box = None
        self.drag_threshold = 0.2
        self.click_start_time = time.time()
        self.step = Vec3(0, 0, 0)

    def update_ui_icons(self):
        """Public function which refreshes all icons in whole UI element"""
        for slot, box in enumerate(self.boxes):
            item = self.container[slot]
            if item is None:
                icon = None
            else:
                icon = inst_id_to_item_icon[item.inst_id]
            box.set_item_icon(icon)

    def make_item_icon(self, item, box):
        """Creates an item icon and puts it in the UI.
        item: Item to make the icon for
        box: ItemBox to put the ItemIcon in
        """
        if item is None:
            return None
        icon = ItemIcon(item, parent=box, scale=(1, 1), position=(0, 0, -2))
        inst_id_to_item_icon[item.inst_id] = icon
        return icon

    def on_click(self):
        hovered_slot = self.get_hovered_slot()
        self.dragging_box = self.boxes[hovered_slot]
        self.dragging_icon = self.dragging_box.icon
        if self.dragging_icon is None:
            return
        self.step = self.dragging_box.get_position(camera.ui) - mouse.position
        self.click_start_time = time.time()

    def get_hovered_slot(self):
        ui_mouse_pos = mouse.position * camera.ui.scale
        rel_mouse_pos = ui_mouse_pos - self.world_position
        slot_world_pos = Vec2(self.world_scale_x, self.world_scale_y) / self.grid_size
        slot = Vec2(rel_mouse_pos[0], rel_mouse_pos[1]) / slot_world_pos
        slot = (int(slot[0]), int(slot[1]))
        return slot[0] - slot[1] * int(self.grid_size[0])

    def input(self, key):
        if key == "left mouse up" and self.dragging_icon is not None:
            # Item was being dragged and was just released
            other_entity = mouse.hovered_entity
            if not isinstance(other_entity, ItemFrame):
                self.dragging_icon.position = Vec3(0, 0, -1)
            else:
                item = self.dragging_icon.item
                my_slot = self.dragging_icon.parent.slot
                hovered_slot = other_entity.get_hovered_slot()
                drop_box = other_entity.boxes[hovered_slot]
                # Clicked and released quickly without moving out of this box
                if my_slot == hovered_slot and time.time() - self.click_start_time < self.drag_threshold:
                    option = item.leftclick
                    if option == "equip":
                        char = self.parent.char
                        other_slot = char.find_auto_equip_slot(item)
                        other_container = char.equipment
                    if option == "unequip":
                        char = self.parent.char
                        other_slot = char.find_auto_inventory_slot()
                        other_container = char.inventory
                # Clicked and released on another box
                else:
                    other_slot = hovered_slot
                    other_container = drop_box.container
                conn = network.server_connection
                network.peer.request_move_item(conn, item.inst_id, other_container.name, other_slot)
            self.dragging_icon = None
            self.dragging_box = None

    def update(self):
        if self.dragging_icon is not None and mouse.position:
            self.dragging_icon.set_position(mouse.position + self.step, camera.ui)

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
        texture = item.icon_path
        texture_path = os.path.join(item_icons_dir, texture)
        load_texture(texture_path)
        super().__init__(*args, origin=(-.5, .5), model='quad', texture=texture, **kwargs)
