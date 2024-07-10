from ursina import *
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
        _equip_item(char, slot, item)
        item["functions"][0] = "unequip"

def _equip_item(char, slot, item):
    """Equips an item assuming the desired slot is empty. Do not use this except for
    initializing a character's equipment when entering world.
    char: Character
    slot: str, equipment slot
    item: Item, item to equip"""
    char.equipment[slot] = item
    apply_stat_change(char, item['stats'])


def replace_items_internal(char, container_name1, slot1, container_name2, slot2):
    """Swap the locations of two items by containers"""
    container1 = getattr(char, container_name1)
    container2 = getattr(char, container_name2)
    item1 = container1[slot1]
    item2 = container2[slot2]

    container2[slot2] = item1
    container1[slot1] = item2

    if container_name1 == "equipment":
        swap_item_stats(char, item2, item1)
        update_primary_option(item2, "unequip")
    else:
        update_primary_option(item2, "equip")
    if container_name2 == "equipment":
        swap_item_stats(char, item1, item2)
        update_primary_option(item1, "unequip")
    else:
        update_primary_option(item1, "equip")

def swap_item_stats(char, item1, item2):
    """Do the stat changes resulting from equipping item 1 and unequipping item 2."""
    stats1 = StatChange() if item1 is None else item1["stats"]
    stats2 = StatChange() if item2 is None else item2["stats"]

    if network.is_main_client():
        apply_stat_change(char, stats1)
        remove_stat_change(char, stats2)
        char.update_max_ratings()
    else:
        conn = network.peer.get_connections()[0]
        if stats1:
            network.peer.remote_apply_stat_change(conn, stats1)
        if stats2:
            network.peer.remote_remove_stat_change(conn, stats2)

def update_primary_option(item, funcname):
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
        """An item is literally just a dict.
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