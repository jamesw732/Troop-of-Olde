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
        self.container = None
        self.slot = None

        self.name = data.get("name", "")
        self.type = data.get("type", "")
        self.info = data.get("info", {})
        self.stats = data.get("stats", {})
        self.stats = Stats(self.stats)
        if self.type in self.type_to_options:
            self.leftclick = self.type_to_options[self.type][0]
        self.icon_name = data.get("icon", "")
        self.model_name = data.get("model", "")

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

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class Container(list):
    def __init__(self, name, items):
        """List[Item] wrapper with some added functionality
        inst_id: network id used to refer to this container across network. Currently unused.
        name: str descriptor of this container
        items: list of Item objects
        """
        self.name = name
        super().__init__([None] * len(items))
        for i, item in enumerate(items):
            self[i] = item

    def __setitem__(self, slot, item):
        super().__setitem__(slot, item)
        if item is not None:
            item.container = self
            item.slot = slot

    def __repr__(self):
        return str([repr(item) for item in self])


def find_auto_equip_slot(char, item):
    """Finds the equipment slot to auto equip item to"""
    exclude_slots = set()
    for slot in item.info["equip_slots"]:
        cur_item = char.equipment[slot]
        if cur_item is None and slot not in exclude_slots:
            return slot
        elif cur_item is not None:
            exclude_slots |= set(cur_item.info["equip_exclude_slots"])
    return item.info["equip_slots"][0]

def find_auto_inventory_slot(char):
    """Finds the inventory slot to auto place item to"""
    try:
        return next((s for s, item in enumerate(char.inventory) if item is None))
    except StopIteration:
        return -1

def get_move_dict(char, to_container, to_slot, from_container, from_slot):
    """Returns a dict of item moves in the format {to_container_name: {from_container_name: item}}"""
    item1 = from_container[from_slot]
    if item1 is None:
        # Should be safe to assume otherwise, but just in case
        return {}
    item2 = to_container[to_slot]
    initial_swaps = [(item1, to_container, to_slot, from_container, from_slot),
                     (item2, from_container, from_slot, to_container, to_slot)]
    # Dict mapping tgt container name to src container name to (item, tgt slot, src slot)
    # Essentially a table of tgt container by src container
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
                    empty_inv_slot = find_auto_inventory_slot(char)
                    if empty_inv_slot < 0:
                        return {}
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
                return {}
    return move_dict
