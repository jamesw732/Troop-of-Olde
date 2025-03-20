from ursina import *
import json
import copy

from . import default_equipment, default_inventory
from .gamestate import gs
# This import might be a problem eventually
from .states.container import IdContainer, container_to_ids, ids_to_container
from .states.state import State, apply_state_diff, remove_state_diff

"""
JSON Structure:
{
    id: {
        "name": name,
        "type": type
        "info": {
            "info1": val1
            "info2": val2, etc
        }
        "stats": {
            "stat1": val1,
            "stat2": val2, etc
        }
        "functions": [funcname1, funcname2, etc]
    }
}
Eventual attrs: on_use (an Effect id), model (a str), texture (a str)

name is required

type is a descriptor of what kind of item this is, tells the code what kind of info to look for. Required. Currently the options are:
weapon
equipment

info is not meant to be directly interoperable with a Character but are essential data about the item. Info depends on the type of item.
(equippable; weapons or equipment)
slot
slots
(weapons)
dmg
delay

stats are attributes that will be copied into an Item object which will be copied directly to a Character object. There should be 100% interoperability between the two, anything that doesn't make sense to be assigned directly as an attribute of a character should go in info. Required for any equippable item. Valid stats are character attributes, a comprehensive list here:
statichealth
staticmana
staticstamina
spellshield
armor
maxspellshield # If spellshield or armor is set, the max must also be set.
maxarmor
bdy
str
dex
ref
int
afire
acold
aelec
apois
adis
haste
speed
casthaste
healmod

functions: Names of functions this item has access to. Optional, if not specified the options are inferred from the type.
"""

# Probably better to have this somewhere else
items_file = os.path.join(os.path.dirname(__file__), "..", "data", "items.json")
with open(items_file) as items:
    items_dict = json.load(items)


class Item(dict):
    type_to_options = {
        "weapon": ["equip", "expunge"],
        "equipment": ["equip", "expunge"]
    }
    option_to_meth = {
        "equip": "auto_equip",
        "unequip": "auto_unequip"
    }

    def __init__(self, item_id):
        """An Item represents the internal state of an in-game item. It is mostly just a dict.
        item_id: items_dict key, int or str (gets casted to a str)
        See JSON structure for valid kwargs"""
        item_id = str(item_id)
        self.id = item_id
        self.icon = None
        data = items_dict[item_id]

        super().__init__(**data)
        # Need to be careful with assigning mutable objects
        if self["type"] in ["weapon", "equipment"]:
            self["stats"] = State("pc_combat", **self.get("stats", {}))
        if "functions" not in self:
            self['functions'] = copy.copy(self.type_to_options.get(self["type"], []))
        if gs.network.peer.is_hosting():
            # Set the instantiated ID.
            # Currently, instantiated item id's are only transmitted to
            # the client upon connection, they will eventually need to be transmitted upon creation.
            # This should probably be outside of this __init__, though.
            self.iiid = gs.network.iiid_counter
            gs.network.iiid_to_item[gs.network.iiid_counter] = self
            gs.network.iiid_counter += 1

# Public functions
def internal_swap(char, container1, slot1, container2, slot2):
    """Handles all the magic necessary to swap two items. Main driving function
    for moving items.

    It is important to treat container1 and slot1 as the source, as the
    corresponding Item cannot be None"""
    item1 = getattr(char, container1)[slot1]
    item2 = getattr(char, container2)[slot2]

    # If we're intentionally equipping offhand, unequip 2h if wearing
    man_unequip_2h = equipping_oh_wearing_2h(char, item1, slot2) \
                     or equipping_oh_wearing_2h(char, item2, slot1)
    # If equipping 2h, also unequip offhand if wearing
    if equipping_2h(item1, container2):
        unequip_offhand(char)
    if equipping_2h(item2, container1):
        unequip_offhand(char)

    internal_move_item(char, item1, container2, slot2, container1)
    handle_stat_updates(char, item1, container2, container1)
    internal_move_item(char, item2, container1, slot1, container2)
    handle_stat_updates(char, item2, container1, container2)
    # Save auto unequipping 2h for last, otherwise position gets screwed up
    if man_unequip_2h:
        iauto_unequip(char, "mh")

def iauto_equip(char, old_container, old_slot):
    """Auto equips an item internally"""
    item = getattr(char, old_container)[old_slot]
    new_slot = find_first_empty_equip(item, char)
    internal_swap(char, old_container, old_slot, "equipment", new_slot)

def iauto_unequip(char, old_slot):
    """Auto unequips an item internally"""
    new_slot = find_first_empty_inventory(char)
    if new_slot == "":
        return
    internal_swap(char, "equipment", old_slot, "inventory", new_slot)

def equip_many_items(char, itemsdict, handle_stats=True):
    """Magically equips all items in itemsdict. Use this only when characters enter world.
    char: Character
    itemsdict: dict mapping equipment slots to Items
    handle_stats: bool, only True when called by server"""
    for slot, item in itemsdict.items():
        internal_move_item(char, item, "equipment", slot, from_container_n="nowhere")
        update_primary_option(item, "unequip")
        if handle_stats:
            handle_stat_updates(char, item, "equipment", "nowhere")

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
        # Skip stat change if staying within equipment
        if from_container_n != "equipment":
            apply_state_diff(char, item["stats"])
    elif from_container_n == "equipment":
        remove_state_diff(char, item["stats"])
    char.update_max_ratings()

# Lower level private functions
def get_primary_option_from_container(item, container):
    """Get intended primary option of an item based on where it is"""
    if item is None or container is None:
        return ""
    if container == "equipment":
        return "unequip"
    elif container == "inventory":
        if item["type"] in ["weapon", "equipment"]:
            return "equip"

def update_primary_option(item, funcname):
    """Overwrite the top option of the item with funcname. Will likely be replaced eventually.
    item: Item
    funcname: str, name of function to replace the top option"""
    if item is None:
        return
    if "functions" not in item:
        item["functions"] = [funcname]
        return
    # This seems really bad. Definitely want to work something better out once
    # item tooltips are a thing
    item["functions"][0] = funcname

def equipping_2h(item, tgt_container):
    return tgt_container == "equipment" and item_is_2h(item)

def unequip_offhand(char):
    """Unequips the offhand, if there is one"""
    # Unequip the offhand too
    offhand = char.equipment["oh"]
    if offhand is not None:
        unequipped = iauto_unequip(char, "oh")
        if not unequipped:
            return False
    return True

def equipping_oh_wearing_2h(char, item, tgt_slot):
    """Equipping an offhand while wearing a 2h weapon. Note that based on how
    auto slot finding is written, this case is only possible if the slot was
    intentionally selected for this item."""
    mh = char.equipment["mh"]
    if mh is None:
        return False
    mh_is_2h = item_is_2h(mh)
    return mh_is_2h and tgt_slot == "oh"

def item_is_2h(item):
    if item is None:
        return False
    return item.get("type") == "weapon" and item.get("info", {}).get("style", "")[:2] == "2h"

def find_first_empty_equip(item, char):
    """Find the correct spot to equip this item to"""
    iteminfo = item.get("info", {})
    if not iteminfo:
        return
    slot = iteminfo.get("slot", "")
    if not slot:
        # Might not have found, that's okay, just check for first empty in slots
        slots = iteminfo.get("slots", [])
        if not slots:
            return ""
        for s in slots:
            i_in_s = char.equipment[s]
            if i_in_s is None or s == "mh" and item_is_2h(i_in_s):
                slot = s
                break
        # None empty, so just take the first
        else:
            slot = slots[0]
    return slot

def find_first_empty_inventory(char):
    """Find the first empty inventory slot"""
    invent = char.inventory
    empty_slots = (str(slot) for slot in range(24) if invent[str(slot)] is None)
    try:
        return next(empty_slots)
    except StopIteration:
        return ""
