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

    def __init__(self, item_id, inst_id=-1):
        """An Item represents the internal state of an in-game item. It is mostly just a dict.
        item_id: items_dict key, int or str (gets casted to a str)
        See JSON structure for valid kwargs"""
        self.item_id = item_id
        data = copy.deepcopy(items_dict[str(item_id)])

        self.name = data.get("name", "")
        self.type = data.get("type", "")
        self.info = data.get("info", {})
        self.stats = data.get("stats", {})
        self.stats = State("pc_combat", **self.stats)
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

        if gs.network.peer.is_hosting():
            # Set the instantiated ID.
            # Currently, instantiated item id's are only transmitted to the client upon player connection,
            # they will eventually need to be transmitted upon creation.
            self.inst_id = gs.network.item_inst_id_ct
            gs.network.item_inst_id_ct += 1
        else:
            self.inst_id = inst_id
        if self.inst_id >= 0:
            gs.network.inst_id_to_item[self.inst_id] = self

    def __str__(self):
        return self.name

# Public functions
def make_item_from_data(item_data):
    """Handles the possible cases for creating an item from id's

    item_data: an item_id, if called by the server.
    If called as an RPC for a client, item_data should be a tuple (item_id, instance_id)
    Also allowed to be an Item, in which case just return item_data"""
    if isinstance(item_data, int):
        # item_data is an id
        if item_data < 0:
            return None
        return Item(item_data)
    elif isinstance(item_data, tuple):
        # item_data is a tuple containing (item_id, inst_id)
        # this is for items created by client, since the server tells the client what the instance id is
        if item_data[0] < 0:
            return None
        return Item(*item_data)
    # otherwise, assume it's an Item already
    return item_data


def internal_swap(char, from_container_n, from_slot, to_container_n, to_slot):
    """Handles all the magic necessary to swap two items. Main driving function
    for moving items."""

    item1 = getattr(char, from_container_n)[from_slot]
    item2 = getattr(char, to_container_n)[to_slot]

    # If we're intentionally equipping offhand, unequip 2h if wearing
    man_unequip_2h = equipping_oh_wearing_2h(char, item1, to_slot) \
                     or equipping_oh_wearing_2h(char, item2, from_slot)
    # If equipping 2h, also unequip offhand if wearing
    if equipping_2h(item1, to_container_n):
        unequip_offhand(char)
    if equipping_2h(item2, from_container_n):
        unequip_offhand(char)

    internal_move_item(char, item1, to_container_n, to_slot, from_container_n)
    handle_stat_updates(char, item1, to_container_n, from_container_n)
    internal_move_item(char, item2, from_container_n, from_slot, to_container_n)
    handle_stat_updates(char, item2, from_container_n, to_container_n)
    # Save auto unequipping 2h for last, otherwise position gets screwed up
    if man_unequip_2h:
        iauto_unequip(char, slot_to_ind["mh"])

def iauto_equip(char, old_container, old_slot):
    """Auto equips an item internally"""
    item = getattr(char, old_container)[old_slot]
    new_slot = find_first_empty_equip(item, char)
    if new_slot > 0:
        internal_swap(char, old_container, old_slot, "equipment", new_slot)

def iauto_unequip(char, old_slot):
    """Auto unequips an item internally"""
    new_slot = find_first_empty_inventory(char)
    if new_slot == "":
        return
    internal_swap(char, "equipment", old_slot, "inventory", new_slot)

def equip_item(char, item, slot, handle_stats=True):
    internal_move_item(char, item, "equipment", slot, from_container_n="nowhere")
    update_primary_option(item, "unequip")
    if handle_stats:
        handle_stat_updates(char, item, "equipment", "nowhere")


def equip_many_items(char, items, handle_stats=True):
    """Magically equips all items in itemsdict. Use this only when characters enter world.
    char: Character
    itemsdict: dict mapping equipment slots to Items
    handle_stats: bool, only True when called by server"""
    for slot, item in enumerate(items):
        equip_item(char, item, slot, handle_stats)

def auto_set_primary_option(item, container_name):
    new_primary_option = get_primary_option_from_container(item, container_name)
    update_primary_option(item, new_primary_option)

# Private functions
def internal_move_item(char, item, to_container_n, to_slot, from_container_n="inventory"):
    """Move an item internally from from_container_n to to_container_n. Does not update stats.

    char: Character
    item: Item
    to_container_n: str, name of target container
    to_slot: str or int, key or index of target container
    from_container_n: str, name of source container
    """
    to_container = getattr(char, to_container_n)
    to_container[to_slot] = item
    auto_set_primary_option(item, to_container_n)

def handle_stat_updates(char, item, to_container_n, from_container_n):
    """Updates stats for an item being equipped or unequipped

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

def equipping_oh_wearing_2h(char, item, tgt_slot):
    """Returns whether we're equipping an offhand while wearing a 2h weapon. Note that based on how
    auto slot finding is written, this case is only possible if the slot was
    intentionally selected for this item."""
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
