from ursina import *
import copy

from .base import *
from ... import *

"""Explanation of terminology used in this file:
Item objects represent the invisible data of an item. They inherit dict and are mostly used just like dicts.
ItemBox objects represent boxes within the inventory
ItemIcon objects represent actual visible items within the inventory
ItemsWindow is the PlayerWindow subframe, the highest ancestor in this file
ItemFrame represents a grid of items, and handles most of the items UI inputs
"""

class ItemsWindow(Entity):
    def __init__(self, char, *args, **kwargs):
        self.char = char
        super().__init__(*args, **kwargs)
        # This is used to normalize lengths relative to the width/height of the ItemsWindow
        # Given a width/length, multiply the length by window_wh_ratio to get the correct
        # length relative to the width
        window_wh_ratio = self.world_scale_x / self.world_scale_y
        # How far away from the edge to put the subcontainers
        edge_margin = 0.025

        # Make equipment subframe
        equip_frame_width = 0.4
        equip_grid_size = Vec2(2, 2)
        equip_box_spacing = 0

        equip_frame_height = get_grid_height(equip_frame_width, equip_grid_size, spacing=equip_box_spacing,
                                             window_wh_ratio=window_wh_ratio)
        equip_frame_scale = Vec3(equip_frame_width, equip_frame_height, 1)
        equip_frame_pos = ((1 - equip_frame_width) / 2, equip_frame_height + edge_margin - 1, -1)

        self.equipment_frame = ItemFrame(equip_grid_size, self.char.equipment,
                                        slot_labels=equipment_slots,
                                        parent=self, position=equip_frame_pos, scale=equip_frame_scale)

        # Make inventory subframe
        inventory_frame_width = 1 - 8 * edge_margin
        inventory_grid_size = (4, 5)
        inventory_box_spacing = 0

        inventory_frame_height = get_grid_height(inventory_frame_width, inventory_grid_size,
                                                 spacing=inventory_box_spacing, window_wh_ratio=window_wh_ratio)
        inventory_position = (4 * edge_margin, -edge_margin, -1)
        inventory_frame_scale = Vec2(inventory_frame_width, inventory_frame_height)

        self.inventory_frame = ItemFrame(inventory_grid_size, self.char.inventory,
                                         parent=self, position=inventory_position, scale=inventory_frame_scale)

        self.container_to_frame = {"equipment": self.equipment_frame,
                                   "inventory": self.inventory_frame}

    def enable_colliders(self):
        self.inventory_frame.collision = True
        self.equipment_frame.collision = True

    def disable_colliders(self):
        self.inventory_frame.collision = False
        self.equipment_frame.collision = False


class ItemFrame(Entity):
    def __init__(self, grid_size, container, slot_labels=[], **kwargs):
        self.grid_size = grid_size
        self.container = container
        # pad the slot labels with empty strings
        self.slot_labels = slot_labels + ([""] * (len(container) - len(slot_labels)))

        self.boxes = [None] * len(container)
        self.icons = [None] * len(container)

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
            self.icons[i] = icon

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
                box.itemicon = None
                box.label.text = self.slot_labels[slot]
                icon = None
            else:
                icon = item.icon
                box.itemicon = icon
                icon.parent = box
                icon.position = Vec3(0, 0, -1)
                box.label.text = ""
            self.icons[slot] = icon

    def make_item_icon(self, item, box):
        """Creates an item icon and puts it in the UI.
        item: Item to make the icon for
        box: ItemBox to put the ItemIcon in
        """
        if item is None:
            return None
        return ItemIcon(item, parent=box, scale=(1, 1), position=(0, 0, -2))

    def on_click(self):
        hovered_slot = self.get_hovered_slot()
        self.dragging_icon = self.icons[hovered_slot]
        self.dragging_box = self.boxes[hovered_slot]
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
            other_container = mouse.hovered_entity
            if not isinstance(other_container, ItemFrame):
                self.dragging_icon.position = Vec3(0, 0, -1)
            else:
                hovered_slot = other_container.get_hovered_slot()
                drop_box = other_container.boxes[hovered_slot]
                # Clicked and released quickly without moving out of this box
                if drop_box == self.dragging_box and time.time() - self.click_start_time < self.drag_threshold:
                    option = self.dragging_icon.item.leftclick
                    meth = Item.option_to_meth[option]
                    getattr(self.dragging_icon, meth)()
                # Clicked and released on another box
                else:
                    self.handle_release_icon(self.dragging_icon, drop_box)
            self.dragging_icon = None
            self.dragging_box = None

    def handle_release_icon(self, my_icon, other_box):
        """Performs checks client-side to make sure an item move is valid, then
        sends request to server. Only called when manually dragging items.

        Expected to have some delay when latency is high. In this case, should
        predict the new locations client-side."""
        other_icon = other_box.icon
        other_slot = other_box.slot

        my_slot = my_icon.parent.slot

        # Should eventually make this handling more general, maybe give ItemBoxes knowledge
        # of what valid items can go in them rather than hardcoding equipment.
        equipping_mine = other_box.container.name == "equipment"
        equipping_other = self.container.name == "equipment"

        # Make sure items can go to new locations if being equipped
        if equipping_other and other_box.icon is not None:
            if my_slot not in other_box.icon.get_equippable_slots():
                my_icon.position = Vec3(0, 0, -1)
                return
        if equipping_mine:
            if other_slot not in my_icon.get_equippable_slots():
                my_icon.position = Vec3(0, 0, -1)
                return
        conn = network.server_connection
        network.peer.request_swap_items(conn, other_box.container.container_id, other_slot,
                                           self.container.container_id, my_slot)

    def update(self):
        if self.dragging_icon is not None and mouse.position:
            self.dragging_icon.set_position(mouse.position + self.step, camera.ui)

class ItemBox(Entity):
    def __init__(self, *args, text="", slot=None, container=None,  **kwargs):
        super().__init__(*args, origin=(-.5, .5), **kwargs)
        self.label = Text(text=text, parent=self, origin=(0, 0), position=(0.5, -0.5, -1),
                          world_scale=(11, 11), color=window_fg_color)

        self.container = container
        self.slot = slot
        self.icon = None


class ItemIcon(Entity):
    """UI Representation of an Item."""
    def __init__(self, item, *args, **kwargs):
        self.item = item
        texture = item.icon_path
        texture_path = os.path.join(item_icons_dir, texture)
        load_texture(texture_path)
        self.item.icon = self
        super().__init__(*args, origin=(-.5, .5), model='quad', texture=texture, **kwargs)

    def auto_equip(self):
        """UI/networking wrapper for Item.internal_autoequip"""
        conn = network.server_connection
        network.peer.request_auto_equip(conn, self.item.inst_id, self.parent.slot,
                                           self.parent.container.container_id)

    def auto_unequip(self):
        """UI/networking wrapper for Item.internal_autounequip"""
        conn = network.server_connection
        network.peer.request_auto_unequip(conn, self.item.inst_id, self.parent.slot)

    def get_equippable_slots(self):
        """Returns available equipment slots for item"""
        return self.item.info.get("equip_slots", [])

