from ursina import *
from ursina.networking import rpc
import json
import copy

from .base import default_equipment, default_inventory
from .gamestate import gs
from .networking.base import network
from .ui.base import ui
# This import might be a problem eventually
from .states.container import InitContainer, container_to_init, init_to_container
from .states.stat_change import StatChange, apply_stat_change, remove_stat_change

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
Eventual attrs: on_use (an Effect), model (a str), texture (a str)

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

    def __init__(self, id):
        """An Item represents the internal state of an in-game item. It is mostly just a dict.
        id: items_dict key, int or str (gets casted to a str)
        See JSON structure for valid kwargs"""
        id = str(id)
        self.id = id
        self.icon = None
        data = items_dict[id]

        super().__init__(**data)
        # Need to be careful with assigning mutable objects
        if self["type"] in ["weapon", "equipment"]:
            self["stats"] = StatChange(**self.get("stats", {}))
        if "functions" not in self:
            self['functions'] = copy.copy(self.type_to_options.get(self["type"], []))
        if network.peer.is_hosting():
            self.uiid = network.uiid_counter
            network.uiid_to_item[network.uiid_counter] = self
            network.uiid_counter += 1


def equip_many_items(char, itemsdict):
    """Magically equips all items in itemsdict. Use this only when characters enter world.
    char: Character
    itemsdict: dict mapping equipment slots to Items"""
    for slot, item in itemsdict.items():
        internal_move_item(char, item, "equipment", slot, old_container_n="nowhere")
        update_primary_option(item, "unequip")

def internal_move_item(char, item, new_container_n, new_slot, old_container_n="inventory"):
    """Move an item internally from old_container_n to new_container_n.

    Updates stats for items being equipped.
    char: Character
    item: Item
    new_container_n: str, name of target container
    new_slot: str or int, key or index of target container
    old_container_n: str, name of source container
    """
    new_container = getattr(char, new_container_n)
    new_container[new_slot] = item
    if item is None:
        return
    if new_container_n == "equipment":
        # Skip stat change if staying within equipment
        if old_container_n != "equipment":
            apply_stat_change(char, item["stats"])
    elif old_container_n == "equipment":
        remove_stat_change(char, item["stats"])
    char.update_max_ratings()


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

def internal_swap(char, container1, slot1, container2, slot2):
    """Combines all functions necessary to be a wrapper for ItemIcon.swap_locs

    It is important to treat container1 and slot1 as the source, as the
    corresponding Item cannot be None"""
    item1 = getattr(char, container1)[slot1]
    item2 = getattr(char, container2)[slot2]

    # If we're intentionally equipping offhand, unequip 2h if wearing
    man_unequip_2h = equipping_oh_wearing_2h(char, item1, slot2)
    # If equipping 2h, also unequip offhand if wearing
    if equipping_2h(item1, container2):
        unequip_offhand(char, item1)

    internal_move_item(char, item1, container2, slot2, container1)
    internal_move_item(char, item2, container1, slot1, container2)
    # Save auto unequipping 2h for last, otherwise position gets screwed up
    if man_unequip_2h:
        iauto_unequip(char, "mh")


def iauto_equip(char, old_container, old_slot):
    """Auto equips an item internally"""
    item = getattr(char, old_container)[old_slot]
    new_slot = find_first_empty_equip(item, char)
    internal_swap(char, old_container, old_slot, "equipment", new_slot)

def iauto_unequip(char, old_slot):
    new_slot = find_first_empty_inventory(char)
    if new_slot == "":
        return
    internal_swap(char, "equipment", old_slot, "inventory", new_slot)

def equipping_2h(item, tgt_container):
    return tgt_container == "equipment" and item_is_2h(item)

def unequip_offhand(char, item):
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
    return item.get("type") == "weapon" and item.get("info", {}).get("style", "")[:2] == "2h"

@rpc(network.peer)
def remote_swap(connection, time_received, container1: str, slot1: str, container2: str, slot2: str):
    """Request host to swap items internally, host will send back updated container states"""
    if not network.peer.is_hosting():
        return
    char = network.connection_to_char[connection]
    internal_swap(char, container1, slot1, container2, slot2)
    for name in set([container1, container2]):
        container = container_to_init(getattr(char, name))
        network.peer.remote_update_container(connection, name, container)

@rpc(network.peer)
def remote_auto_equip(connection, time_received, itemid: int, old_slot: str, old_container: str):
    """Request host to automatically equip a given item."""
    char = network.connection_to_char[connection]
    iauto_equip(char, old_container, old_slot)
    for name in set([old_container, "equipment"]):
        container = container_to_init(getattr(char, name))
        network.peer.remote_update_container(connection, name, container)

@rpc(network.peer)
def remote_auto_unequip(connection, time_received, itemid: int, old_slot: str):
    """Request host to automatically unequip a given item."""
    char = network.connection_to_char[connection]
    iauto_unequip(char, old_slot)
    for name in ["equipment", "inventory"]:
        container = container_to_init(getattr(char, name))
        network.peer.remote_update_container(connection, name, container)

@rpc(network.peer)
def remote_update_container(connection, time_received, container_name: str, container: InitContainer):
    """Update internal containers and visual containers

    Mimic most of the process in ItemIcon.swap_locs for hosts, but
    this will only be done by non-hosts"""
    if network.peer.is_hosting():
        return
    internal_container = init_to_container(container)
    update_container(container_name, internal_container)
    # loop = internal_container.items()
    # container = getattr(gs.pc, container_name)
    # for slot, item in loop:
    #     container[slot] = item
    #     new_primary_option = get_primary_option_from_container(item, container_name)
    #     update_primary_option(item, new_primary_option)

    # ui.playerwindow.items.update_ui_icons(container_name, loop=loop)

def update_container(container_name, internal_container):
    loop = internal_container.items()
    container = getattr(gs.pc, container_name)
    for slot, item in loop:
        container[slot] = item
        new_primary_option = get_primary_option_from_container(item, container_name)
        update_primary_option(item, new_primary_option)

    ui.playerwindow.items.update_ui_icons(container_name, loop=loop)