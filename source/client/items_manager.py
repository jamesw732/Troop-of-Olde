from ursina import *

from ..item import *


class ItemsManager(Entity):
    """Defines all operations on Items and Containers."""
    def __init__(self, global_containers, animation_system):
        super().__init__()
        self.inst_id_to_item = global_containers.inst_id_to_item
        self.animation_system = animation_system

    def make_item(self, item_mnem, inst_id):
        item = Item(item_mnem, inst_id)
        self.inst_id_to_item[inst_id] = item
        return item

    def overwrite_char_equipment(self, char, items):
        if len(char.equipment) != len(items):
            return
        for slot, item in enumerate(items):
            char.equipment[slot] = item
            if item is not None:
                item.leftclick = "unequip"
            self.animation_system.set_equipment_slot(char, slot, item)

    def overwrite_char_inventory(self, char, items):
        if len(char.inventory) != len(items):
            return
        for slot, item in enumerate(items):
            char.inventory[slot] = item
            if item is not None:
                item.leftclick = "equip"

