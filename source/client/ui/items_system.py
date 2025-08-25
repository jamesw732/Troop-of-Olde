from ursina import *

from .items import *
from ... import *


class ItemsSystem(Entity):
    """Owns all ItemFrames and ItemIcons, and handles visual item movement."""
    def __init__(self, char):
        super().__init__()
        self.char = char
        self.inst_id_to_item_icon = {}
        self.item_frames = {}

        self.dragging_icon = None
        self.dragging_box = None
        self.drag_threshold = 0.2
        self.click_start_time = time.time()
        self.step = Vec3(0, 0, 0)

    def make_item_frame(self, grid_size, container, slot_labels=[], **kwargs):
        """Creates an ItemFrame and adds it to self.item_frames."""
        frame = ItemFrame(grid_size, container, slot_labels=slot_labels,
                          start_dragging=self.start_dragging_icon, **kwargs)
        self.item_frames[container.name] = frame
        for i, box in enumerate(frame.boxes):
            item = container[i]
            icon = self.make_item_icon(item, box)
        return frame

    def make_item_icon(self, item, box):
        """Creates an ItemIcon and adds it to self.inst_id_to_item_icon."""
        if item is None:
            icon = None
        else:
            icon = ItemIcon(item, parent=box, scale=(1, 1), position=(0, 0, -2))
            self.inst_id_to_item_icon[item.inst_id] = icon
        box.set_item_icon(icon)
        return icon

    def update_item_icons(self):
        """Update position of item icons based on current state of containers"""
        for frame in self.item_frames.values():
            for slot, box in enumerate(frame.boxes):
                item = frame.container[slot]
                if item is None:
                    icon = None
                else:
                    icon = self.inst_id_to_item_icon[item.inst_id]
                box.set_item_icon(icon)

    def start_dragging_icon(self, icon, box):
        self.dragging_box = box
        self.dragging_icon = icon
        if self.dragging_icon is None:
            return
        self.step = self.dragging_box.get_position(camera.ui) - mouse.position
        self.click_start_time = time.time()

    def input(self, key):
        if key == "left mouse up" and self.dragging_icon is not None:
            # Item was being dragged and was just released
            other_entity = mouse.hovered_entity
            if not isinstance(other_entity, ItemFrame):
                self.dragging_icon.position = Vec3(0, 0, -1)
            else:
                item = self.dragging_icon.item
                my_slot = self.dragging_box.slot
                my_container = self.dragging_box.parent.container
                hovered_slot = other_entity.get_hovered_slot()
                drop_box = other_entity.boxes[hovered_slot]
                # Clicked and released quickly without moving out of this box
                if my_slot == hovered_slot and \
                        time.time() - self.click_start_time < self.drag_threshold:
                    option = item.leftclick
                    if option == "equip":
                        char = self.char
                        other_slot = find_auto_equip_slot(char, item)
                        other_container = char.equipment
                    if option == "unequip":
                        char = self.char
                        other_slot = find_auto_inventory_slot(char)
                        other_container = char.inventory
                # Clicked and released on another box
                else:
                    other_slot = hovered_slot
                    other_container = drop_box.container
                container_swap_locs(self.char, other_container, other_slot, my_container, my_slot)
                self.update_item_icons()
                conn = network.server_connection
                network.peer.request_move_item(conn, item.inst_id, other_container.name, other_slot)
            self.dragging_icon = None
            self.dragging_box = None

    def update(self):
        if self.dragging_icon is not None and mouse.position:
            self.dragging_icon.set_position(mouse.position + self.step, camera.ui)

