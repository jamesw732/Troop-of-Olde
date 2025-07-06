from ursina import *
import json
import copy

from .base import default_equipment, default_inventory, slot_to_ind, equipment_slots, data_path
from .network import network
from .states import Stats

# Eventually, this will be a database connection rather than a json stored in memory
items_file = os.path.join(data_path, "items.json")
with open(items_file) as items:
    items_dict = json.load(items)


class Item:
    type_to_options = {
        "weapon": ["equip"],
        "equipment": ["equip"]
    }
    option_to_meth = {
        "equip": "auto_equip",
        "unequip": "auto_unequip"
    }

    def __init__(self, item_id, inst_id):
        """An Item represents the internal state of an in-game item. It is mostly just a dict.
        item_id: items_dict key, int or str (gets casted to a str)
        See JSON structure for valid kwargs
        item_id: int, id corresponding to an entry in the database; not unique WRT item instances
        inst_id: unique id used to refer to this item over the network"""
        self.item_id = item_id
        self.inst_id = inst_id
        network.inst_id_to_item[self.inst_id] = self
        data = copy.deepcopy(items_dict[str(item_id)])

        self.name = data.get("name", "")
        self.type = data.get("type", "")
        self.info = data.get("info", {})
        self.stats = data.get("stats", {})
        self.stats = Stats(self.stats)
        if self.type in self.type_to_options:
            self.leftclick = self.type_to_options[self.type][0]
        self.icon_path = data.get("icon", "")
        self.icon = None

        # remove "slot", when there's just one make "slots" a singleton list
        if "slots" in self.info:
            self.info["slots"] = [slot_to_ind[slot] if isinstance(slot, str) else slot
                                  for slot in self.info["slots"]]

    def get_valid_move(self, to_container, to_slot):
        """Get whether this item can go to to_slot in to_container
        to_container: intended Container to move this item to
        to_slot: intended slot within to_container to move this item to"""
        # extend this as new types are added, or add a field of Item specifying equipment
        if self.type in ["weapon"] and to_container.name == "equipment":
            if to_slot not in self.info["slots"]:
                return False
        return True

    def handle_stats(self, char, to_container, from_container=[]):
        """Handle necessary char stat changes caused by moving to to_container
        char: Character who is equipping/unequipping this item
        to_container: intended Container to move this item to
        to_slot: intended slot within to_container to move this item to
        from_container: Container currently storing this item, optional"""
        if to_container.name == "equipment":
            # If equipping from elsewhere, add stats
            # But only apply stat change if not swapping between equipment
            if not isinstance(from_container, Container) or from_container.name != "equipment":
                self.stats.apply_diff(char)
        elif isinstance(from_container, Container) and from_container.name == "equipment":
            # If removing from equipment, remove stats
            self.stats.apply_diff(char, remove=True)
        char.update_max_ratings()

    def auto_set_leftclick(self, container):
        """Automatically set the left-click option of item"""
        if self is None or container is None or container.name is None:
            return
        primary_option = "equip"
        if container.name == "equipment":
            primary_option = "unequip"
        elif container.name == "inventory":
            if self.type in ["weapon"]:
                primary_option = "equip"
        self.leftclick = primary_option

    def __str__(self):
        return self.name

class Container(list):
    def __init__(self, container_id, name, items):
        self.container_id = container_id
        self.name = name
        super().__init__(items)
        network.inst_id_to_container[self.container_id] = self

    def get_first_empty(self, item=None, extra_includes=[]):
        """Find the first empty slot in this container
        If can't find any, return -1, which should be treated as nan
        item: if equipping, need to know the item's stats
        extra_includes: slots that are occupied but we still want to return if hit"""
        if self.name == "equipment":
            if item is None:
                return -1
            valid_slots = item.info.get("slots", [])
            for s in valid_slots:
                if self[s] is None or s in extra_includes:
                    return s
        else:
            for s, it in enumerate(self):
                if it is None or s in extra_includes:
                    return s
        return -1

def internal_autoequip(char, container, slot):
    """Auto equips an item internally"""
    item = container[slot]
    # Find the correct slot to equip to
    equipping_mh_wpn = item.type == "weapon" and slot_to_ind["mh"] in item.info["slots"]
    mh_slot = slot_to_ind["mh"]
    wearing_2h = char.equipment[mh_slot] is not None \
            and char.equipment[mh_slot].info["style"][:2] == "2h"
    if equipping_mh_wpn and wearing_2h:
        new_slot = slot_to_ind["mh"]
    else:
        new_slot = char.equipment.get_first_empty(item)
        if new_slot < 0:
            new_slot = item.info.get("slots", [])[0]
    # Perform the move
    full_item_move(char, char.equipment, new_slot, container, slot)

def internal_autounequip(char, old_slot):
    """Auto unequips an item internally"""
    new_slot = char.inventory.get_first_empty()
    if new_slot < 0:
        new_slot = item.info.get("slots", [])[0]
    full_item_move(char, char.inventory, new_slot, char.equipment, old_slot)

def full_item_move(char, to_container, to_slot, from_container, from_slot):
    """Move an item and perform all consequences of the move."""
    item1 = from_container[from_slot]
    if item1 is None:
        # Should be safe to assume otherwise, but just in case
        return
    # Store the necessary moves. All moves formatted (item, to_container, to_slot, from_container)
    moves = [(item1, to_container, to_slot, from_container)]
    item2 = to_container[to_slot]
    moves.append((item2, from_container, from_slot, to_container))
    if to_container.name == "equipment":
        # If equipping a 2h, also unequip offhand
        if item1.type == "weapon" and item1.info["style"][:2] == "2h":
            oh = char.equipment[slot_to_ind["oh"]]
            if isinstance(oh, Item):
                extra_includes = []
                if char.equipment[slot_to_ind["mh"]] is None:
                    extra_includes = [from_slot]
                oh_tgt_slot = char.inventory.get_first_empty(oh, extra_includes=extra_includes)
                if oh_tgt_slot >= 0:
                    # Move the offhand out, replace it with None
                    moves.append((oh, char.inventory, oh_tgt_slot, char.equipment))
                    moves.append((None, char.equipment, slot_to_ind["oh"], char.inventory))
        # If equipping an offhand, also unequip 2h in mainhand
        if equipment_slots[to_slot] == "oh":
            mh = char.equipment[slot_to_ind["mh"]]
            if mh is not None and mh.info["style"][:2] == "2h":
                extra_includes = [from_slot]
                mh_tgt_slot = char.inventory.get_first_empty(mh, extra_includes=extra_includes)
                if mh_tgt_slot >= 0:
                    # Move the 2h out, replace it with None
                    moves.append((mh, char.inventory, mh_tgt_slot, char.equipment))
                    moves.append((None, char.equipment, slot_to_ind["mh"], char.inventory))
    if from_container.name == "equipment":
        # If unequipping a 1h mainhand onto a 2h, also unequip offhand
        if item2 is not None and item2.type == "weapon" and item2.info["style"][:2] == "2h":
            oh = char.equipment[slot_to_ind["oh"]]
            oh_tgt_slot = char.inventory.get_first_empty(oh)
            moves.append((oh, char.inventory, oh_tgt_slot, char.equipment))
            moves.append((None, char.equipment, slot_to_ind["oh"], char.inventory))
    # Check consequences are valid before actually moving anything
    for move in moves:
        item = move[0]
        to_container = move[1]
        to_slot = move[2]
        from_container = move[3]
        if item is not None and not item.get_valid_move(to_container, to_slot):
            return
    # Make all moves and necessary changes
    for move in moves:
        item = move[0]
        to_container = move[1]
        to_slot = move[2]
        from_container = move[3]
        to_container[to_slot] = item
        if item is not None:
            item.handle_stats(char, to_container, from_container)
            item.auto_set_leftclick(to_container)

