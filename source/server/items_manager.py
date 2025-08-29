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
    
