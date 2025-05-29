from ursina import *
import copy

from .base import *
from ..base import equipment_slots
from ..base import slot_to_ind
from ..gamestate import gs
from ..item import *

"""Explanation of terminology used in this file:
Item, named items, represent the invisible data of an item. They inherit dict and are mostly used just like dicts.
ItemBox, named boxes, represent boxes within the inventory
ItemBox.container_name is the name of the internal container that contains Item objects. For now, should only be "inventory" or "equipment"
ItemIcon, named icons or itemicons, represent actual visible items within the inventory
slot is the position within the internal container (so a str key if equipment, or an int index if inventory)
"""

class ItemsWindow(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player = gs.pc

        # This is used to normalize lengths relative to the width/height of the ItemsWindow
        # Given a width/length, multiply the length by window_wh_ratio to get the correct
        # length relative to the width
        window_wh_ratio = self.world_scale_x / self.world_scale_y
        # How far away from the edge to put the subcontainers
        edge_margin = 0.025

        # Make equipment subframe
        # ============PARAMETERS==================
        # For minor changes, these are the numbers to tweak
        # How much of the window should the equipped subframe take up
        # The second dimension is only used for spacing
        equip_frame_width = 0.4
        # Number of boxes in the grid
        equip_grid_size = Vec2(2, 2)
        # % of width of box used as spacing between boxes
        equip_box_spacing = 0
        # Where in the grid the gear slots go
        equipped_positions = [
            Vec3(0, 0, -1),
            Vec3(1, 0, -1),
            Vec3(0, -1, -1),
            Vec3(1, -1, -1),
        ]
        # ============CODE=================
        grid_ratio = equip_grid_size[0] / equip_grid_size[1]
        # compute the height of the frame WRT window given width, grid size, and spacing
        # x is the width of a single box WRT the window
        x = equip_frame_width / (equip_grid_size[0] + equip_box_spacing * (equip_grid_size[0] - 1))
        # y is the height of a single box WRT the window
        y = x * window_wh_ratio
        equip_frame_height = y * (equip_grid_size[1] + equip_box_spacing * (equip_grid_size[1] - 1))
        # height of equip frame relative to the width
        equip_frame_scale = Vec3(equip_frame_width, equip_frame_height, 1)
        equip_frame_pos = ((1 - equip_frame_width) / 2, equip_frame_height + edge_margin - 1)
        self.equipped_frame = Entity(parent=self, origin=(-.5, .5),
                                        position=equip_frame_pos,
                                        scale=equip_frame_scale)
        # Compure the scale of the boxes with respect to the frame
        box_w = 1 / (equip_grid_size[0] + equip_box_spacing * (equip_grid_size[0] - 1))
        box_h = 1 / (equip_grid_size[1] + equip_box_spacing * (equip_grid_size[1] - 1))

        equip_box_scale = Vec3(box_w, box_h, 1)

        self.equipment_boxes = [
            ItemBox(text=equipment_slots[i], slot=i, container_name="equipment",
                           parent=self.equipped_frame,
                           position=pos * ((1 + equip_box_spacing) * equip_box_scale),
                           scale=equip_box_scale, color=slot_color)
                for i, pos in enumerate(equipped_positions)
        ]

        # Make inventory subframe
        # ===========PARAMETERS=============
        # Width of the inventory frame relative to the window
        inventory_frame_width = 1 - 8 * edge_margin
        # Dimensions of the inventory slots
        inventory_grid_size = (4, 5)
        # Position of the subframe
        inventory_position = (4 * edge_margin, -edge_margin, -1)
        # ===========CODE==============
        grid_ratio = inventory_grid_size[0] / inventory_grid_size[1]
        inventory_frame_height = inventory_frame_width / grid_ratio * window_wh_ratio
        inventory_frame_scale = Vec2(inventory_frame_width, inventory_frame_height)

        self.inventory_positions = [Vec3(i, -j, -1)
                                    for j in range(inventory_grid_size[1])
                                    for i in range(inventory_grid_size[0])]

        self.inventory_subframe = Entity(parent=self, origin=(-.5, .5),
                                        position=inventory_position,
                                        scale=inventory_frame_scale)

        inventory_box_scale = Vec3(1 / inventory_grid_size[0], 1 / inventory_grid_size[1], 1)

        self.inventory_boxes = [
            ItemBox(slot=i, container_name="inventory",
                    parent=self.inventory_subframe,
                    position=pos * inventory_box_scale,
                    scale=inventory_box_scale, color=slot_color)
            for i, pos in enumerate(self.inventory_positions)
        ]

        for slot in self.equipment_boxes:
            grid(slot, num_rows=1, num_cols=1, color=color.black)
        for slot in self.inventory_boxes:
            grid(slot, num_rows=1, num_cols=1, color=color.black)

        self.item_icons = []

        self.make_char_items()


    def make_char_items(self):
        """Reads player inventory and equipment and outputs to UI"""
        for i, item in enumerate(self.player.inventory):
            self.make_item_icon(item, self.inventory_boxes[i])
        for i, item in enumerate(self.player.equipment):
            if item is not None:
                self.equipment_boxes[i].label.text = ""
            self.make_item_icon(item, self.equipment_boxes[i])

    def make_item_icon(self, item, parent):
        """Creates an item icon and puts it in the UI.
        Assumes the internals are already taken care of.
        item: Item
        ui_container: list of ItemSlots
        internal_container: list of Items
        slot: str or int; key or index to containers"""
        if item is None:
            return
        if "icon" in item:
            texture = os.path.join(effect_icons_dir, item["icon"])
            load_texture(texture)
            icon = ItemIcon(item, parent=parent, scale=(1, 1),
                            position=(0, 0, -2), texture=item["icon"])
        else:
            icon = ItemIcon(item, parent=parent, scale=(1, 1),
                            position=(0, 0, -2), color=color.gray)
        parent.itemicon = icon
        self.item_icons.append(icon)

    def enable_colliders(self):
        for box in self.equipment_boxes:
            box.collision = True
        for box in self.inventory_boxes:
            box.collision = True
        for icon in self.item_icons:
            icon.collision = True

    def disable_colliders(self):
        for box in self.equipment_boxes:
            box.collision = False
        for box in self.inventory_boxes:
            box.collision = False
        for icon in self.item_icons:
            icon.collision = False

    def update_ui_icons(self, container_name):
        ui_container = getattr(self, container_name + "_boxes")
        for box in ui_container:
            box.refresh_icon()


class ItemBox(Entity):
    def __init__(self, *args, text="", slot=None, container_name="", **kwargs):
        super().__init__(*args, origin=(-.5, .5), model='quad', collider='box', **kwargs)
        if text:
            self.label = Text(text=text, parent=self, origin=(0, 0), position=(0.5, -0.5, -1),
                             world_scale=(11, 11), color=window_fg_color)
        self.container_name = container_name
        self.container = getattr(gs.pc, container_name)
        self.slot = slot
        self.itemicon = None

    def refresh_icon(self):
        item = self.container[self.slot]
        if item is None:
            self.itemicon = None
            if self.container_name == "equipment":
                self.label.text = equipment_slots[self.slot]
            return
        icon = item.icon
        self.itemicon = icon
        icon.parent = self
        icon.position = Vec3(0, 0, -1)
        if self.container_name == "equipment":
            self.label.text = ""

class ItemIcon(Entity):
    """UI Representation of an Item. Logically, above Item. The reason for this is that
    it makes sense for an Item to not have an ItemIcon, but it does not make sense for an ItemIcon
    to not have an Item. Reversing the dependence would make the rest of this module harder to implement."""
    def __init__(self, item, *args, **kwargs):
        super().__init__(*args, origin=(-.5, .5), model='quad', collider='box', **kwargs)
        self.item = item
        self.item.icon = self
        self.window = self.parent.parent.parent

        self.previous_parent = None
        self.clicked = False
        self.clicked_time = 0
        self.drag_threshold = 0.2
        self.dragging = False
        self.step = Vec3(0, 0, 0)

    def update(self):
        if self.clicked:
            if held_keys["left mouse"]:
                # Wait until we're sure the player is dragging
                if self.clicked_time < self.drag_threshold:
                    self.clicked_time += time.dt
                # When we are sure, start dragging
                elif not self.dragging:
                    self.dragging = True
                    self.collision = False
            else:
                self.clicked_time = 0
                self.clicked = False
                # Item was being dragged but was just released
                if self.dragging:
                    self.dragging = False
                    drop_to = mouse.hovered_entity
                    if isinstance(drop_to, ItemBox):
                        self.swap_locs(other_box=drop_to)
                    elif isinstance(drop_to, ItemIcon):
                        self.swap_locs(other_icon=drop_to)
                    else:
                        self.position = Vec3(0, 0, -1)
                    self.collision = True
                # Item was not being dragged, execute its top function
                else:
                    option = self.item["functions"][0]
                    meth = Item.option_to_meth[option]
                    getattr(self, meth)()
            if self.dragging:
                if mouse.position:
                    self.set_position(mouse.position + self.step, camera.ui)

    def swap_locs(self, other_icon=None, other_box=None):
        """Swaps the contents of two ItemBoxes. Main driving function of inventory movement.

        Must specify one of other_icon or other_box. General process after determining the
        relevant inputs is this (only by main client):
        1. Check if the items can go to the new locations
        2. Remove/add text to equipment slots, if applicable
        3. Swap box contents
        4. Swap icon parents, and reposition to (0, 0, 0)
        5. Update primary options (if moved between inventory and equipment, for example)
        6. Do function call for the internal move
        other_icon: ItemIcon
        other_box: ItemSlot"""
        if other_icon is None and other_box is None:
            return
        if other_box is None:
            other_box = other_icon.parent
        elif other_icon is None:
            other_icon = other_box.itemicon
        other_container = other_box.container_name
        other_slot = other_box.slot
        other_item = other_icon.item if isinstance(other_icon, ItemIcon) else None
        my_container = self.parent.container_name
        my_slot = self.parent.slot
        equipping_mine = other_container == "equipment"
        equipping_other = my_container == "equipment"

        # Make sure items can go to new locations if being equipped
        if equipping_other and other_icon is not None:
            other_item_slots = other_icon.get_item_slots()
            if my_slot not in other_item_slots:
                self.position = Vec3(0, 0, -1)
                return False
        if equipping_mine:
            my_item_slots = self.get_item_slots()
            if other_slot not in my_item_slots:
                self.position = Vec3(0, 0, -1)
                return False

        conn = gs.network.server_connection
        gs.network.peer.request_swap_items(conn, my_container, my_slot, other_container, other_slot)

    def auto_equip(self):
        """UI wrapper for Item.iauto_equip"""
        conn = gs.network.server_connection
        gs.network.peer.request_auto_equip(conn, self.item.inst_id, self.parent.slot, self.parent.container_name)

    def auto_unequip(self):
        """UI wrapper for Item.iauto_unequip"""
        conn = gs.network.server_connection
        gs.network.peer.request_auto_unequip(conn, self.item.inst_id, self.parent.slot)

    def get_item_slots(self):
        """Unified way to get the available slots of an equippable item"""
        iteminfo = self.item.get("info", {})
        slot = iteminfo.get("slot")
        if slot is not None:
            return [slot]
        slots = iteminfo.get("slots", [])
        return slots

    def on_click(self):
        self.clicked = True
        self.step = self.get_position(camera.ui) - mouse.position
