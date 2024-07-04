from ursina import *

from .base import *
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
            "ear": Vec3(0, 0, -3),
            "head": Vec3(1/3, 0, -3),
            "neck": Vec3(0, -1/7, -3),
            "chest": Vec3(1/3, -1/7, -3),
            "back": Vec3(2/3, -1/7, -3),
            "legs": Vec3(1/3, -2/7, -3),
            "hands": Vec3(0, -3/7, -3),
            "feet": Vec3(1/3, -3/7, -3),
            "ring": Vec3(2/3, -3/7, -3),
            "mh": Vec3(0, -2/7, -3),
            "oh": Vec3(2/3, -2/7, -3),
            "ammo": Vec3(2/3, 0, -3)
        }
        self.equipped_slots = {
            slot: ItemSlot(text=slot, parent=self.equipped_subframe, origin=(-.5, .5),
                           position=loc * Vec2(1.2, 1.66), scale=(1/3, 1/7), model='quad', color=slot_color)
            for slot, loc in self.equipped_locs.items()
        }

        self.inventory_subframe = Entity(parent=self, origin=(-.5, .5),
                                        position=(edge_margin + 0.45, -edge_margin, -2),
                                        scale=(sq_size * 4, sq_size * 7 * square_ratio))
        
        self.inventory_locs = [(i / 4, -j / 7, -3) for i in range(4) for j in range(6)]
        self.inventory_slots = [ItemSlot(parent=self.inventory_subframe, origin=(-.5, .5),
                           position=loc, scale=(1/4, 1/7), model='quad', color=slot_color)
                           for loc in self.inventory_locs]

        # Eventually, don't grid whole equipped, just do a 1x1 grid on each slot
        for slot in self.equipped_slots.values():
            grid(slot, num_rows=1, num_cols=1, color=color.black)
        for slot in self.inventory_slots:
            grid(slot, num_rows=1, num_cols=1, color=color.black)

class ItemSlot(Entity):
    def __init__(self, *args, text="", **kwargs):
        super().__init__(*args, **kwargs)
        if text:
            self.text = Text(text=text, parent=self, origin=(0, 0), position=(0.5, -0.5, -4),
                             world_scale=(11, 11), color=window_fg_color)