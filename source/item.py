from ursina import *
import json
import copy

from .base import default_equipment, default_inventory, slot_to_ind, equipment_slots
from .gamestate import gs
# This import might be a problem eventually
from .states.state import State

# Eventually, this will be a database connection rather than a json stored in memory
items_file = os.path.join(os.path.dirname(__file__), "..", "data", "items.json")
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
        gs.network.inst_id_to_item[self.inst_id] = self
        data = copy.deepcopy(items_dict[str(item_id)])

        self.name = data.get("name", "")
        self.type = data.get("type", "")
        self.info = data.get("info", {})
        self.stats = data.get("stats", {})
        self.stats = State("item_stats", self.stats)
        if self.type in self.type_to_options:
            self.leftclick = self.type_to_options[self.type][0]
        self.icon_path = data.get("icon", "")
        self.icon = None

        # remove "slot", when there's just one make "slots" a singleton list
        if "slots" in self.info:
            self.info["slots"] = [slot_to_ind[slot] if isinstance(slot, str) else slot
                                  for slot in self.info["slots"]]

    def __str__(self):
        return self.name

class ServerItem(Item):
    def __init__(self, item_id):
        # Set the instance ID. Server needs to externally transmit this upon item creation.
        self.inst_id = gs.network.item_inst_id_ct
        gs.network.item_inst_id_ct += 1
        super().__init__(item_id, self.inst_id)

class Container(list):
    def __init__(self, container_id, name, items):
        self.container_id = container_id
        self.name = name
        super().__init__(items)
        gs.network.inst_id_to_container[self.container_id] = self

class ServerContainer(Container):
    def __init__(self, name, items):
        container_id = gs.network.container_inst_id_ct
        gs.network.container_inst_id_ct += 1
        super().__init__(container_id, name, items)

# New code
def internal_autoequip(char, container, slot):
    """Auto equips an item internally"""
    item = container[slot]
    new_slot = get_first_empty(char.equipment, item)
    if new_slot < 0:
        new_slot = item.info.get("slots", [])[0]
    full_item_move(char, char.equipment, new_slot, container, slot)

def internal_autounequip(char, old_slot):
    """Auto unequips an item internally"""
    new_slot = get_first_empty(char.inventory)
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
                oh_tgt_slot = get_first_empty(char.inventory, oh)
                if oh_tgt_slot >= 0:
                    # Move the offhand out, replace it with None
                    moves.append((oh, char.inventory, oh_tgt_slot, char.equipment))
                    moves.append((None, char.equipment, slot_to_ind["oh"], char.inventory))
        # If equipping an offhand, also unequip 2h in mainhand
        if equipment_slots[to_slot] == "oh":
            mh = char.equipment[slot_to_ind["mh"]]
            if mh.info["style"][:2] == "2h":
                mh_tgt_slot = get_first_empty(char.inventory, mh)
                if mh_tgt_slot >= 0:
                    # Move the 2h out, replace it with None
                    moves.append((mh, char.inventory, mh_tgt_slot, char.equipment))
                    moves.append((None, char.equipment, slot_to_ind["mh"], char.inventory))
    # Check consequences are valid before actually moving anything
    for move in moves:
        if not get_valid_move(*move[:-1]):
            return
    # Make all moves and necessary changes
    for move in moves:
        item = move[0]
        to_container = move[1]
        to_slot = move[2]
        from_container = move[3]
        to_container[to_slot] = item
        handle_stats(char, item, to_container, from_container)
        auto_set_leftclick(item, to_container)

def get_first_empty(container, item=None):
    """Find the first empty"""
    if container.name == "equipment":
        if item is None:
            return -1
        valid_slots = item.info.get("slots", [])
        for s in valid_slots:
            cur_item = container[s]
            if cur_item is None:
                return s
    else:
        for s, it in enumerate(container):
            if it is None:
                return s
    return -1

def get_valid_move(item, to_container, to_slot):
    # Get whether item can go to to_slot
    # extend this as new types are added, or add a field of Item specifying equipment
    if isinstance(item, Item) and item.type in ["weapon"] and to_container.name == "equipment":
        if to_slot not in item.info["slots"]:
            return False
    return True

def handle_stats(char, item, to_container, from_container=[]):
    if item is None:
        return
    if to_container.name == "equipment":
        # Only apply stat change if not swapping between equipment
        if not isinstance(from_container, Container) or from_container.name != "equipment":
            item.stats.apply_diff(char)
    elif isinstance(from_container, Container) and from_container.name == "equipment":
        item.stats.apply_diff(char, remove=True)
    char.update_max_ratings()

def auto_set_leftclick(item, container):
    """Automatically set the left-click option of item"""
    if item is None or container is None or container.name is None:
        return
    primary_option = "equip"
    if container.name == "equipment":
        primary_option = "unequip"
    elif container.name == "inventory":
        if item.type in ["weapon"]:
            primary_option = "equip"
    item.leftclick = primary_option
