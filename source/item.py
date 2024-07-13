from ursina import *
from ursina.networking import rpc
import json

from .networking.base import network
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


def equip_many_items(char, itemsdict):
    """Magically equips all items in itemsdict. Use this only when characters enter world.
    char: Character
    itemsdict: dict mapping equipment slots to Items"""
    for slot, item in itemsdict.items():
        internal_move_item(char, item, "equipment", slot, old_container_n="nowhere")


def internal_move_item(char, item, new_container_n, new_slot, old_container_n="inventory"):
    """Move an item internally from old_container_n to new_container_n
    char: Character
    item: Item
    new_container_n: str, name of target container
    new_slot: str or int, key or index of target container
    old_container_n: str, name of source container
    """
    new_container = getattr(char, new_container_n)
    new_container[new_slot] = item
    # Don't attempt the stat changes or anything
    if item is None:
        return
    if new_container_n == "equipment":
        update_primary_option(item, "unequip")
        # Skip stat change if staying within equipment
        if old_container_n != "equipment":
            apply_stat_change(char, item["stats"])
    elif old_container_n == "equipment":
        remove_stat_change(char, item["stats"])
        update_primary_option(item, "equip")
    else:
        update_primary_option(item, "equip")
    char.update_max_ratings()


@rpc(network.peer)
def remote_equip(connection, time_received, uuid: int, item_id: str, slot: str, extra: StatChange=StatChange()):
    """Create a new item based on an item id and any "extra" stuff.

    Call this whenever an item is equipped by the client. Does not think about unequipping.
    Right now, a new item is created each time, but it might be better to implement
    an item instance id system eventually. It seems very possible to make the server lag
    by equipping items constantly."""
    if not network.peer.is_hosting():
        return
    char = network.uuid_to_char[uuid]
    item = Item(item_id)
    char.equipment[slot] = item
    apply_stat_change(char, item["stats"])
    char.update_max_ratings()

def update_primary_option(item, funcname):
    """Overwrite the top option of the item with funcname. Will likely be replaced eventually.
    item: Item
    funcname: str, name of function to replace the top option"""
    if item is None:
        return
    if "functions" not in item:
        item["functions"] = [funcname]
        return
    item["functions"][0] = funcname

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
        data = items_dict[id]

        super().__init__(**data)
        # Need to be careful with assigning mutable objects
        if self["type"] in ["weapon", "equipment"]:
            self["stats"] = StatChange(**self.get("stats", {}))
        if "functions" not in self:
            self['functions'] = copy(self.type_to_options.get(self["type"], []))