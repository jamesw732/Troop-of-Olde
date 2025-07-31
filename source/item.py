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

    def __repr__(self):
        return str([item.__repr__() for item in self])
