from .. import *


class ItemsManager:
    """Provides an interface for item creation and system-level stat changes from item movement"""
    def __init__(self, gamestate):
        self.inst_id_to_item = gamestate.inst_id_to_item
        self.item_inst_id_ct = 0

    def make_item(self, item_mnem):
        inst_id = self.item_inst_id_ct
        self.item_inst_id_ct += 1
        def on_destroy():
            del self.inst_id_to_item[inst_id]
        item = Item(item_mnem, inst_id, on_destroy=on_destroy)
        self.inst_id_to_item[inst_id] = item
        return item

    def perform_item_moves(self, char, move_dict):
        """Performs all moves from a dict with format {to_container_name: {from_container_name: item}}"""
        for item, tgt_slot, src_slot in move_dict.get("equipment", {}).get("inventory", {}):
            char.equipment[tgt_slot] = item
            if item is not None:
                item.stats.apply_diff(char)
        for item, tgt_slot, src_slot in move_dict.get("equipment", {}).get("equipment", {}):
            char.equipment[tgt_slot] = item
        for item, tgt_slot, src_slot in move_dict.get("inventory", {}).get("equipment", {}):
            char.inventory[tgt_slot] = item
            if item is not None:
                item.stats.apply_diff(char, remove=True)
        for item, tgt_slot, src_slot in move_dict.get("inventory", {}).get("inventory", {}):
            char.inventory[tgt_slot] = item
        char.update_max_ratings()
