from ursina import *

from ..item import *


class ItemsManager(Entity):
    """Defines all operations on Items and Containers."""
    def __init__(self, gamestate, animation_system):
        super().__init__()
        self.inst_id_to_item = gamestate.inst_id_to_item
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

    def perform_item_moves(self, char, move_dict):
        """Performs all moves from a dict with format {to_container_name: {from_container_name: item}}

        Only used for client-side prediction of item movement. Does not update stats."""
        for item, tgt_slot, src_slot in move_dict.get("equipment", {}).get("inventory", {}):
            char.equipment[tgt_slot] = item
            if item is not None:
                item.leftclick = "unequip"
        for item, tgt_slot, src_slot in move_dict.get("equipment", {}).get("equipment", {}):
            char.equipment[tgt_slot] = item
        for item, tgt_slot, src_slot in move_dict.get("inventory", {}).get("equipment", {}):
            char.inventory[tgt_slot] = item
            if item is not None:
                item.leftclick = "equip" # This may need some better logic some day
        for item, tgt_slot, src_slot in move_dict.get("inventory", {}).get("inventory", {}):
            char.inventory[tgt_slot] = item
