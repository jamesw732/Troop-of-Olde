from ursina import *

from .base import *
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

        square_ratio = self.world_scale_x / self.world_scale_y
        edge_margin = 0.05

        sq_size = 0.9 / 7 / square_ratio

        self.equipped_subframe = Entity(parent=self, origin=(-.5, .5),
                                        position=(edge_margin, -edge_margin, -1),
                                        scale=(sq_size * 3, sq_size * 7 * square_ratio))

        self.equipped_positions = {
            "ear": Vec3(0, 0, -1),
            "head": Vec3(1/3, 0, -1),
            "neck": Vec3(0, -1/7, -1),
            "chest": Vec3(1/3, -1/7, -1),
            "back": Vec3(2/3, -1/7, -1),
            "legs": Vec3(1/3, -2/7, -1),
            "hands": Vec3(0, -3/7, -1),
            "feet": Vec3(1/3, -3/7, -1),
            "ring": Vec3(2/3, -3/7, -1),
            "mh": Vec3(0, -2/7, -1),
            "oh": Vec3(2/3, -2/7, -1),
            "ammo": Vec3(2/3, 0, -1)
        }
        self.equipped_boxes = {
            slot: ItemBox(text=slot, slot=slot, container_name="equipment",
                           parent=self.equipped_subframe, position=pos * Vec2(1.2, 1.66),
                           scale=(1/3, 1/7), color=slot_color)
            for slot, pos in self.equipped_positions.items()
        }

        self.inventory_subframe = Entity(parent=self, origin=(-.5, .5),
                                        position=(edge_margin + 0.45, -edge_margin, -1),
                                        scale=(sq_size * 4, sq_size * 7 * square_ratio))

        self.inventory_positions = [(i / 4, -j / 7, -1) for j in range(6) for i in range(4)]
        self.inventory_boxes = [ItemBox(slot=i, container_name="inventory",
                                        parent=self.inventory_subframe,
                                        position=pos, scale=(1/4, 1/7), color=slot_color)
                                for i, pos in enumerate(self.inventory_positions)]

        # Eventually, don't grid whole equipped, just do a 1x1 grid on each slot
        for slot in self.equipped_boxes.values():
            grid(slot, num_rows=1, num_cols=1, color=color.black)
        for slot in self.inventory_boxes:
            grid(slot, num_rows=1, num_cols=1, color=color.black)

        self.item_icons = []

        self.make_char_items()

    def make_char_items(self):
        """Reads player inventory and equipment and outputs to UI"""
        for icon in self.item_icons:
            destroy(icon)
        for i, item in enumerate(self.player.inventory):
            self.make_item_icon(item, self.inventory_boxes[i])
        for k, item in self.player.equipment.items():
            if item is not None:
                self.equipped_boxes[k].label.text = ""
            self.make_item_icon(item, self.equipped_boxes[k])

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
            texture = os.path.join(icons_dir, item["icon"])
            load_texture(texture)
            icon = ItemIcon(item, parent=parent, scale=(1, 1),
                            position=(0, 0, -2), texture=item["icon"])
        else:
            icon = ItemIcon(item, parent=parent, scale=(1, 1),
                            position=(0, 0, -2), color=color.gray)
        parent.itemicon = icon
        self.item_icons.append(icon)

    def enable_colliders(self):
        for box in self.equipped_boxes.values():
            box.collision = True
        for box in self.inventory_boxes:
            box.collision = True
        for icon in self.item_icons:
            icon.collision = True

    def disable_colliders(self):
        for box in self.equipped_boxes.values():
            box.collision = False
        for box in self.inventory_boxes:
            box.collision = False
        for icon in self.item_icons:
            icon.collision = False

class ItemBox(Entity):
    def __init__(self, *args, text="", container=None, slot=None, container_name="", **kwargs):
        super().__init__(*args, origin=(-.5, .5), model='quad', collider='box', **kwargs)
        if text:
            self.label = Text(text=text, parent=self, origin=(0, 0), position=(0.5, -0.5, -1),
                             world_scale=(11, 11), color=window_fg_color)
        self.container_name = container_name
        self.slot = slot
        self.itemicon = None

class ItemIcon(Entity):
    """UI Representation of an Item. Logically, above Item. The reason for this is that
    it makes sense for an Item to not have an ItemIcon, but it does not make sense for an ItemIcon
    to not have an Item. Reversing the dependence would make the rest of this module harder to implement."""
    def __init__(self, item, *args, **kwargs):
        super().__init__(*args, origin=(-.5, .5), model='quad', collider='box', **kwargs)
        self.item = item
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
                        self.swap_locs(other_item=drop_to)
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

    def swap_locs(self, other_item=None, other_box=None):
        """Swaps the contents of two ItemBoxes. Main driving function of inventory movement.
        Must specify one of other_item or other_box.
        other_item: ItemIcon
        other_box: ItemSlot"""
        if other_item is None and other_box is None:
            return
        if other_box is None:
            other_box = other_item.parent
        elif other_item is None:
            other_item = other_box.itemicon
        other_container = other_box.container_name
        other_slot = other_box.slot
        my_container = self.parent.container_name
        my_slot = self.parent.slot
        equipping_mine = other_container == "equipment"
        equipping_other = my_container == "equipment"

        # Make sure items can go to new locations
        # Equipment checks:
        if equipping_other and other_item is not None:
            other_item_slots = other_item.get_item_slots()
            if my_slot not in other_item_slots:
                return
        if equipping_mine:
            my_item_slots = self.get_item_slots()
            if other_slot not in my_item_slots:
                self.position = Vec3(0, 0, -1)
                return

        # Remove/add text if necessary:
        if equipping_other and other_item is None:
            self.parent.label.text = my_slot
        if equipping_mine:
            other_box.label.text = ""

        # Swap ItemSlots' ItemIcons
        other_box.itemicon = self
        self.parent.itemicon = other_item

        # Reparent and reposition icons
        if other_item is not None:
            other_item.parent = self.parent
            other_item.position = Vec3(0, 0, -2)

        self.parent = other_box
        self.position = Vec3(0, 0, -2)

        player = gs.pc
        # Do the internal, non-graphical move
        replace_slot(player, my_container, my_slot, other_container, other_slot)

    def auto_equip(self):
        # Find the right slot
        # First, just look for "slot"
        iteminfo = self.item.get("info")
        if not iteminfo:
            return
        slot = iteminfo.get("slot")
        if not slot:
            # Might not have found, that's okay, just check for first empty in slots
            slots = iteminfo.get("slots", [])
            if not slots:
                return
            for s in slots:
                if self.window.equipped_boxes[s].itemicon is None:
                    slot = s
                    break
            # None empty, so just take the first
            else:
                slot = slots[0]
        self.swap_locs(other_box=self.window.equipped_boxes[slot])

    def auto_unequip(self):
        inventory_icons = [s.itemicon for s in self.window.inventory_boxes]
        try:
            first_empty_idx = inventory_icons.index(None)
        except ValueError:
            return
        empty_slot = self.window.inventory_boxes[first_empty_idx]
        self.swap_locs(other_box=empty_slot)

    def get_item_slots(self):
        iteminfo = self.item.get("info")
        if not iteminfo:
            return
        slot = iteminfo.get("slot")
        if slot is not None:
            return [slot]
        return iteminfo.get("slots", [])
