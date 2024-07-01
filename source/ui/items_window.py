from ursina import *

from .base import *
from .header import Header
from ..gamestate import gs

class ItemsWindow(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        square_ratio = self.world_scale_x / self.world_scale_y
        edge_margin = 0.05

        sq_size = 0.9 / 7 / square_ratio

        self.equipped_subframe = Entity(parent=self, origin=(-.5, .5),
                                        position=(edge_margin, -edge_margin, -2),
                                        scale=(sq_size * 3, sq_size * 7 * square_ratio))

        self.equipped_locs = {
            "head": (1/3, 0, -3),
        }
        self.equipped_slots = {
            slot: ItemSlot(parent=self.equipped_subframe, origin=(-.5, .5),
                           position=loc, scale=(1/3, 1/7), model='quad')
            for slot, loc in self.equipped_locs.items()
        }

        self.inventory_subframe = Entity(parent=self, origin=(-.5, .5),
                                        position=(edge_margin + 0.45, -edge_margin, -2),
                                        scale=(sq_size * 4, sq_size * 7 * square_ratio))
        
        self.inventory_locs = [(i / 4, -j / 7, -3) for i in range(4) for j in range(7)]
        self.inventory_slots = [ItemSlot(parent=self.inventory_subframe, origin=(-.5, .5),
                           position=loc, scale=(1/4, 1/7), model='quad') for loc in self.inventory_locs]

        # Eventually, don't grid whole equipped, just do a 1x1 grid on each slot
        grid(self.equipped_subframe, num_rows=7, num_cols=3, color=color.black)
        grid(self.inventory_subframe, num_rows=7, num_cols=4, color=color.black)

class ItemSlot(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)