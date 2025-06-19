from ursina import *
import json
import copy

from .base import default_equipment, default_inventory, slot_to_ind
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
        self.functions = copy.copy(self.type_to_options.get(self.type, []))
        self.icon_path = data.get("icon", "")
        self.icon = None

        # remove "slot", when there's just one make "slots" a singleton list
        if "slot" in self.info:
            if isinstance(self.info["slot"], str):
                self.info["slot"] = slot_to_ind[self.info["slot"]]
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

# Public functions
def internal_swap(char, from_container, from_slot, to_container, to_slot):
    """Handles all the magic necessary to swap the contents of two item locations.
    Main driving function for moving items."""
    from_container_n = from_container.name
    item1 = from_container[from_slot]
    to_container_n = to_container.name
    item2 = to_container[to_slot]

    # If we're intentionally equipping offhand, unequip 2h if wearing
    man_unequip_2h = equipping_oh_wearing_2h(char, item1, to_container_n, to_slot) \
                     or equipping_oh_wearing_2h(char, item2, from_container_n, from_slot)
    # If equipping 2h, also unequip offhand if wearing
    if equipping_2h(item1, to_container_n):
        unequip_offhand(char)
    if equipping_2h(item2, from_container_n):
        unequip_offhand(char)

    internal_move_item(char, item1, to_container_n, to_slot, from_container_n)
    internal_move_item(char, item2, from_container_n, from_slot, to_container_n)
    # Save auto unequipping 2h for last, otherwise position gets screwed up
    if man_unequip_2h:
        iauto_unequip(char, slot_to_ind["mh"])

def iauto_equip(char, old_container, old_slot):
    """Auto equips an item internally"""
    item = old_container[old_slot]
    new_slot = find_first_empty_equip(item, char)
    if new_slot > 0:
        internal_swap(char, old_container, old_slot, char.equipment, new_slot)

def iauto_unequip(char, old_slot):
    """Auto unequips an item internally"""
    new_slot = find_first_empty_inventory(char)
    if new_slot == "":
        return
    internal_swap(char, char.equipment, old_slot, char.inventory, new_slot)

def internal_move_item(char, item, to_container_n, to_slot, from_container_n, handle_stats=True):
    """Internally overwrite an item slot with item.

    char: Character
    item: Item
    to_container_n: str, name of target container
    to_slot: str or int, key or index of target container
    from_container_n: str, name of source container
    handle_stats: whether or not to compute stat changes. Generally, True for server, False for client.
    """
    to_container = getattr(char, to_container_n)
    to_container[to_slot] = item
    auto_set_primary_option(item, to_container_n)
    if handle_stats:
        handle_stat_updates(char, item, to_container_n, from_container_n)

# Private functions
def auto_set_primary_option(item, container_name):
    new_primary_option = get_primary_option_from_container(item, container_name)
    update_primary_option(item, new_primary_option)

def handle_stat_updates(char, item, to_container_n, from_container_n):
    """Essentially a wrapper for item.stats.apply_diff(char) with logic for
    whether the item is getting equipped or not.

    char: Character
    item: Item
    to_container_n: str, name of target container
    from_container_n: str, name of source container"""
    if item is None:
        return
    if to_container_n == "equipment":
        # Only apply stat change if not swapping between equipment
        if from_container_n != "equipment":
            item.stats.apply_diff(char)
    elif from_container_n == "equipment":
        item.stats.apply_diff(char, remove=True)
    char.update_max_ratings()

# Lower level private functions
def get_primary_option_from_container(item, container):
    """Get intended primary option of an item based on where it is"""
    if item is None or container is None:
        return ""
    if container == "equipment":
        return "unequip"
    elif container == "inventory":
        if item.type in ["weapon", "equipment"]:
            return "equip"

def update_primary_option(item, funcname):
    """Overwrite the top option of the item with funcname. Will likely be replaced eventually.
    item: Item
    funcname: str, name of function to replace the top option"""
    if item is None:
        return
    # This is really bad. Definitely want to work something better out once items have multiple options
    # and item tooltips are a thing
    item.functions = [funcname]

def equipping_2h(item, tgt_container):
    return tgt_container == "equipment" and item_is_2h(item)

def unequip_offhand(char):
    """Unequips the offhand, if there is one"""
    # Unequip the offhand too
    offhand = char.equipment[slot_to_ind["oh"]]
    if offhand is not None:
        unequipped = iauto_unequip(char, slot_to_ind["oh"])
        if not unequipped:
            return False
    return True

def equipping_oh_wearing_2h(char, item, tgt_container_n, tgt_slot):
    """Returns whether we're equipping an offhand while wearing a 2h weapon. Note that based on how
    auto slot finding is written, this case is only possible if the slot was
    intentionally selected for this item."""
    if tgt_container_n != "equipment":
        return
    mh = char.equipment[slot_to_ind["mh"]]
    if mh is None:
        return False
    return item_is_2h(mh) and tgt_slot == slot_to_ind["oh"]

def item_is_2h(item):
    if item is None:
        return False
    return item.type == "weapon" and item.info.get("style", "")[:2] == "2h"

def find_first_empty_equip(item, char):
    """Find the correct spot to equip this item to"""
    # may need to test this more carefully, item being None causes crashes rarely when double clicking items
    if item is None:
        return -1
    if not item.info:
        return
    slot = item.info.get("slot", "")
    if not slot:
        # Might not have found, that's okay, just check for first empty in slots
        slots = item.info.get("slots", [])
        if not slots:
            # This is guaranteed to not work right now
            return -1
        for s in slots:
            cur_item = char.equipment[s]
            if cur_item is None or s == slot_to_ind["mh"] and item_is_2h(cur_item):
                slot = s
                break
        # None empty, so just take the first
        else:
            slot = slots[0]
    return slot

def find_first_empty_inventory(char):
    """Find the first empty inventory slot"""
    empty_slots = (slot for slot in range(28) if char.inventory[slot] is None)
    try:
        return next(empty_slots)
    except StopIteration:
        return ""
