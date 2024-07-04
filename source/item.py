from ursina import *
import json

from .ui.main import ui

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

info is not meant to be directly interoperable with a Character but are essential data about the item. Info depends :
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
    """Equips all items in itemsdict
    char: Character
    itemsdict: dict mapping equipment slots to Items"""
    for slot, item in itemsdict.items():
        equip_item(char, slot, item)

def equip_item(char, slot, item=None, idx=None):
    """Equips an item assuming the desired slot is empty
    char: Character
    slot: str, equipment slot
    item: Item, item to equip, optional if idx is specified
    idx: int, location of item within inventory. Skip if equipping items from spawn."""
    if char.equipment[slot] or (item is None and idx is None):
        return
    # Assume we're equipping from inventory if and only if idx is specified
    if idx is not None:
        if item is None:
            item = char.inventory[idx]
        char.inventory[idx] = None
    # If we're equipping from, say, spawn in, we don't need to reset an inventory slot
    char.equipment[slot] = item
    _apply_stats(char, item['stats'])

def replace_slot(char, slot, replace_idx):
    """Equips an item by replacing an existing item"""
    new_item = char.inventory[replace_idx]
    old_item = char.equipment[slot]
    char.inventory[replace_idx] = old_item
    char.equipment[slot] = new_item
    _remove_stats(char, old_item['stats'])
    _apply_stats(char, new_item['stats'])

def unequip_slot(char, slot):
    """Unequips an item into a necessarily empty inventory slot"""
    item = char.equipment[slot]
    if item:
        _remove_stats(char, item['stats'])
        try:
            open_slot = char.inventory.index(None)
            char.inventory[open_slot] = item
            char.equipment[slot] = None
            _remove_stats(char, item['stats'])
        # IE inventory was full
        except ValueError:
            ui.gamewindow.add_message("Inventory full, cannot unequip")

class Item(dict):
    type_to_options = {
        "weapon": ["equip", "expunge"],
        "equipment": ["equip", "expunge"]
    }

    name_to_function = {
        "equip": replace_slot
    }

    def __init__(self, id=None, **kwargs):
        """An item is literally just a dict.
        name: str, name of item,
        slots: str, name of equipped items slot,
        stats: dict, maps character stats to ints"""
        if id is not None:
            super().__init__(**items_dict[id])
        else:
            super().__init__(**kwargs)
        if "stats" not in self and self.type in ["weapon", "equipment"]:
            self['stats'] = {}
        if "functions" not in self:
            self['functions'] = self.types_to_options.get([self.type], [])

def _apply_stats(char, stats):
    for statname, val in stats.items():
        original_val = getattr(char, statname)
        setattr(char, statname, original_val + val)

def _remove_stats(char, stats):
    for statname, val in stats.items():
        original_val = getattr(char, statname)
        setattr(char, statname, original_val - val)