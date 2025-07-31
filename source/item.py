from ursina import *
import json
import copy

from .base import slot_to_ind, equipment_slots, data_path
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

    def __init__(self, item_mnem, inst_id, on_destroy=lambda: None):
        """An Item represents the internal state of an in-game item. It is mostly just a dict.
        item_id: int, id corresponding to an entry in the database; not unique WRT item instances
        inst_id: unique id used to refer to this item over the network
        on_destroy: operations to perform once an Item is destroyed, currently unused"""
        self.item_mnem = item_mnem
        self.inst_id = inst_id
        data = copy.deepcopy(items_dict[item_mnem])
        self.on_destroy = on_destroy

        self.name = data.get("name", "")
        self.type = data.get("type", "")
        self.info = data.get("info", {})
        self.stats = data.get("stats", {})
        self.stats = Stats(self.stats)
        if self.type in self.type_to_options:
            self.leftclick = self.type_to_options[self.type][0]
        self.icon_path = data.get("icon", "")
        self.icon = None

        if self.type == "weapon":
            hands = self.info.get("style", "1h melee")[:2]
            if "equip_slots" in self.info:
                self.info["equip_slots"] = [slot_to_ind[slot] if isinstance(slot, str) else slot
                                      for slot in self.info["equip_slots"]]
            else:
                if hands == "1h":
                    self.info["equip_slots"] = [slot_to_ind[slot] for slot in ["mh", "oh"]]
                else:
                    self.info["equip_slots"] = [slot_to_ind["mh"]]
            if "equip_exclude_slots" in self.info:
                self.info["equip_exclude_slots"] = [slot_to_ind[slot] if isinstance(slot, str) else slot
                                      for slot in self.info["equip_exclude_slots"]]
            else:
                if hands == "1h":
                    self.info["equip_exclude_slots"] = []
                else:
                    self.info["equip_exclude_slots"] = [slot_to_ind["oh"]]

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

    def __repr__(self):
        return self.name

class Container(list):
    def __init__(self, inst_id, name, items):
        """List[Item] wrapper with some added functionality
        container_id: network id used to refer to this container across network
        name: str descriptor of this container
        items: list of Item objects
        """
        self.inst_id = inst_id
        self.name = name
        super().__init__(items)

    def overwrite_items(self, other):
        """Overwrites own items with other container's"""
        if len(self) != len(other):
            return
        for slot, item in enumerate(other):
            self[slot] = item
            if item is not None:
                item.auto_set_leftclick(self)

    def get_first_empty(self, item=None, extra_includes=[]):
        """Find the first empty slot in this container
        If can't find any, return -1, which should be treated as nan
        item: if equipping, need to know the item's stats
        extra_includes: slots that are occupied but we still want to return if hit"""
        if self.name == "equipment":
            if item is None:
                return -1
            valid_slots = item.info.get("equip_slots", [])
            for s in valid_slots:
                if self[s] is None or s in extra_includes:
                    return s
        else:
            for s, it in enumerate(self):
                if it is None or s in extra_includes:
                    return s
        return -1

    def __repr__(self):
        return str([item.__repr__() for item in self])


def container_swap_locs(char, to_container, to_slot, from_container, from_slot):
    """Swap two indices of containers (possibly same or different) if possible.

    Handles specific-container logic such as equipping 2-handed weapons also removing
    offhand."""
    item1 = from_container[from_slot]
    if item1 is None:
        # Should be safe to assume otherwise, but just in case
        return
    item2 = to_container[to_slot]
    initial_swaps = [(item1, to_container, to_slot, from_container, from_slot),
                     (item2, from_container, from_slot, to_container, to_slot)]
    # Dict mapping tgt container name to src container name to (item, tgt slot, src slot)
    move_dict = dict()
    def move_dict_insert(item, tgt_container, tgt_slot, src_container, src_slot):
        """Takes a move in flat structure and puts it in move_dict"""
        if tgt_container.name not in move_dict:
            move_dict[tgt_container.name] = {}
        if src_container.name not in move_dict[tgt_container.name]:
            move_dict[tgt_container.name][src_container.name] = []
        move_dict[tgt_container.name][src_container.name].append((item, tgt_slot, src_slot))
    for item, tgt_container, tgt_slot, src_container, src_slot in initial_swaps:
        move_dict_insert(item, tgt_container, tgt_slot, src_container, src_slot)
    # Compute all consequences of moving item to equipment, particularly for 2h
    if "equipment" in move_dict:
        if "inventory" in move_dict["equipment"]:
            moves = move_dict["equipment"]["inventory"]
            for item, tgt_slot, src_slot in list(moves):
                if item is None:
                    continue
                # Unequip items equipped to slots used by this item
                for exclude_slot in item.info["equip_exclude_slots"]:
                    item_to_move = char.equipment[exclude_slot]
                    if item_to_move is None:
                        continue
                    empty_inv_slot = char.find_auto_inventory_slot()
                    if empty_inv_slot < 0:
                        return
                    move_dict_insert(item_to_move, char.inventory, empty_inv_slot,
                                     char.equipment, exclude_slot)
                    move_dict_insert(None, char.equipment, exclude_slot,
                                     char.inventory, empty_inv_slot)
                # Unequip items equipped to another slot that need tgt_slot
                for slot, multislot_item in enumerate(char.equipment):
                    if multislot_item is None:
                        continue
                    for exclude_slot in multislot_item.info["equip_exclude_slots"]:
                        if exclude_slot == tgt_slot:
                            move_dict_insert(multislot_item, char.inventory, src_slot,
                                             char.equipment, slot)
                            move_dict_insert(None, char.equipment, slot,
                                             char.inventory, src_slot)
    # Validate equipment moves
    for src_container, moves in move_dict.get("equipment", {}).items():
        for item, tgt_slot, src_slot in moves:
            if item is None:
                continue
            if tgt_slot not in item.info["equip_slots"]:
                return
    for item, tgt_slot, src_slot in move_dict.get("equipment", {}).get("inventory", {}):
        char.equipment[tgt_slot] = item
        if item is not None:
            item.leftclick = "unequip"
            item.stats.apply_diff(char)
    for item, tgt_slot, src_slot in move_dict.get("equipment", {}).get("equipment", {}):
        char.equipment[tgt_slot] = item
    for item, tgt_slot, src_slot in move_dict.get("inventory", {}).get("equipment", {}):
        char.inventory[tgt_slot] = item
        if item is not None:
            item.leftclick = "equip" # This may need some better logic some day
            item.stats.apply_diff(char, remove=True)
    for item, tgt_slot, src_slot in move_dict.get("inventory", {}).get("inventory", {}):
        char.inventory[tgt_slot] = item
    char.update_max_ratings()
