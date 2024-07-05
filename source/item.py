from ursina import *
import json


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

# Define public functions here
def equip_many_items(char, itemsdict):
    """Magically equips all items in itemsdict. Use this only when characters enter world.
    char: Character
    itemsdict: dict mapping equipment slots to Items"""
    for slot, item in itemsdict.items():
        _equip_item(char, slot, item)
        item["functions"][0] = "unequip"

def replace_slot(char, container1, slot1, container2, slot2):
    """Swap the locations of two items by containers"""
    item1 = container1[slot1]
    item2 = container2[slot2]

    container2[slot2] = item1
    container1[slot1] = item2

    if isinstance(container1, dict):
        _apply_stats(char, item2)
        _remove_stats(char, item1)
        if item2 is not None:
            item2["functions"][0] = "unequip"
    elif item2 is not None:
        item2["functions"][0] = "equip"
    if isinstance(container2, dict):
        _apply_stats(char, item1)
        _remove_stats(char, item2)
        if item1 is not None:
            item1["functions"][0] = "unequip"
    elif item1 is not None:
        item1["functions"][0] = "equip"

class Item(dict):
    type_to_options = {
        "weapon": ["equip", "expunge"],
        "equipment": ["equip", "expunge"]
    }
    option_to_meth = {
        "equip": "auto_equip",
        "unequip": "auto_unequip"
    }

    def __init__(self, id=None, **kwargs):
        """An item is literally just a dict.
        id: items_dict key
        See JSON structure for valid kwargs"""
        if id is not None:
            super().__init__(**items_dict[id])
        else:
            super().__init__(**kwargs)
        if "stats" not in self and self.type in ["weapon", "equipment"]:
            self['stats'] = {}
        if "functions" not in self:
            self['functions'] = copy(self.type_to_options.get(self["type"], []))

def _equip_item(char, slot, item):
    """Equips an item assuming the desired slot is empty. Do not use this except for
    initializing a character's equipment when entering world.
    char: Character
    slot: str, equipment slot
    item: Item, item to equip"""
    char.equipment[slot] = item
    _apply_stats(char, item)

def _apply_stats(char, item):
    if item is None:
        return
    stats = item.get("stats", {})
    for statname, val in stats.items():
        original_val = getattr(char, statname)
        setattr(char, statname, original_val + val)

def _remove_stats(char, item):
    if item is None:
        return
    stats = item.get("stats", {})
    for statname, val in stats.items():
        original_val = getattr(char, statname)
        setattr(char, statname, original_val - val)