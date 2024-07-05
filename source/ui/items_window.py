from ursina import *

from .base import *
from ..gamestate import gs
from ..item import *

class ItemsWindow(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player = gs.pc.character

        square_ratio = self.world_scale_x / self.world_scale_y
        edge_margin = 0.05

        sq_size = 0.9 / 7 / square_ratio

        self.equipped_subframe = Entity(parent=self, origin=(-.5, .5),
                                        position=(edge_margin, -edge_margin, -1),
                                        scale=(sq_size * 3, sq_size * 7 * square_ratio))

        self.equipped_locs = {
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
        self.equipped_slots = {
            slot: ItemSlot(text=slot, container=self.player.equipment, slot=slot,
                           parent=self.equipped_subframe, position=loc * Vec2(1.2, 1.66),
                           scale=(1/3, 1/7), color=slot_color)
            for slot, loc in self.equipped_locs.items()
        }

        self.inventory_subframe = Entity(parent=self, origin=(-.5, .5),
                                        position=(edge_margin + 0.45, -edge_margin, -1),
                                        scale=(sq_size * 4, sq_size * 7 * square_ratio))

        self.inventory_locs = [(i / 4, -j / 7, -1) for j in range(6) for i in range(4)]
        self.inventory_slots = [ItemSlot(container=self.player.inventory, slot=i,
                                         parent=self.inventory_subframe,
                                         position=loc, scale=(1/4, 1/7), color=slot_color)
                                for i, loc in enumerate(self.inventory_locs)]

        # Eventually, don't grid whole equipped, just do a 1x1 grid on each slot
        for slot in self.equipped_slots.values():
            grid(slot, num_rows=1, num_cols=1, color=color.black)
        for slot in self.inventory_slots:
            grid(slot, num_rows=1, num_cols=1, color=color.black)

        self.item_icons = []

        self.make_char_items()

    def make_char_items(self):
        """Reads player inventory and equipment and outputs to UI"""
        for icon in self.item_icons:
            destroy(icon)
        for i, item in enumerate(self.player.inventory):
            self.make_item_icon(item, self.inventory_slots[i])
        for k, item in self.player.equipment.items():
            if item is not None:
                self.equipped_slots[k].label.text = ""
            self.make_item_icon(item, self.equipped_slots[k])

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
        for slot in self.equipped_slots.values():
            slot.collision = True
        for slot in self.inventory_slots:
            slot.collision = True
        for icon in self.item_icons:
            icon.collision = True

    def disable_colliders(self):
        for slot in self.equipped_slots.values():
            slot.collision = False
        for slot in self.inventory_slots:
            slot.collision = False
        for icon in self.item_icons:
            icon.collision = False

class ItemSlot(Entity):
    def __init__(self, *args, text="", container=None, slot=None, **kwargs):
        super().__init__(*args, origin=(-.5, .5), model='quad', collider='box', **kwargs)
        if text:
            self.label = Text(text=text, parent=self, origin=(0, 0), position=(0.5, -0.5, -1),
                             world_scale=(11, 11), color=window_fg_color)
        self.container = container
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
                    if isinstance(drop_to, ItemSlot):
                        self.swap_locs(other_slot=drop_to)
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

    def swap_locs(self, other_item=None, other_slot=None):
        """Swaps parents of this item and another item, and also swaps internally.
        Must specify one of other_item or other_slot.
        other_item: ItemIcon
        other_slot: ItemSlot"""
        if other_item is None and other_slot is None:
            return
        if other_slot is None:
            other_slot = other_item.parent
        elif other_item is None:
            other_item = other_slot.itemicon
        other_container = other_slot.container
        other_loc = other_slot.slot
        my_container = self.parent.container
        my_loc = self.parent.slot

        # Make sure items can go to new locations
        # Equipment checks:
        if isinstance(my_container, dict) and other_item is not None:
            other_item_slots = other_item.get_item_slots()
            if my_loc not in other_item_slots:
                return
        if isinstance(other_container, dict):
            my_item_slots = self.get_item_slots()
            if other_loc not in my_item_slots:
                self.position = Vec3(0, 0, -1)
                return

        # Remove/add text if necessary:
        if isinstance(my_container, dict) and other_item is None:
            self.parent.label.text = my_loc
        if isinstance(other_container, dict):
            other_slot.label.text = ""

        # Swap ItemSlots' ItemIcons
        other_slot.itemicon = self
        self.parent.itemicon = other_item

        # Reparent and reposition icons
        if other_item is not None:
            other_item.parent = self.parent
            other_item.position = Vec3(0, 0, -2)

        self.parent = other_slot
        self.position = Vec3(0, 0, -2)

        player = gs.pc.character
        # Do the internal, non-graphical move
        replace_slot(player, my_container, my_loc, other_container, other_loc)

    def auto_equip(self):
        # Item.Slot.Subframe.Window
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
                if self.window.equipped_slots[s].itemicon is None:
                    slot = s
                    break
            # None empty, so just take the first
            else:
                slot = slots[0]
        self.swap_locs(other_slot=self.window.equipped_slots[slot])

    def auto_unequip(self):
        # Item.Slot.Subframe.Window
        inventory_icons = [s.itemicon for s in self.window.inventory_slots]
        try:
            # inventory_icons = map(lambda s: s.itemicon, self.window.inventory_slots)
            first_empty_idx = inventory_icons.index(None)
        except ValueError:
            return
        empty_slot = self.window.inventory_slots[first_empty_idx]
        self.swap_locs(other_slot=empty_slot)

    def get_item_slots(self):
        iteminfo = self.item.get("info")
        if not iteminfo:
            return
        slot = iteminfo.get("slot")
        if slot is not None:
            return [slot]
        return iteminfo.get("slots", [])
