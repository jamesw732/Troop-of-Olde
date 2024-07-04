from ursina import *

from .base import *
from ..gamestate import gs
from ..item import *

class ItemsWindow(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        square_ratio = self.world_scale_x / self.world_scale_y
        edge_margin = 0.05

        sq_size = 0.9 / 7 / square_ratio

        self.equipped_subframe = Entity(parent=self, origin=(-.5, .5),
                                        position=(edge_margin, -edge_margin, -1),
                                        scale=(sq_size * 3, sq_size * 7 * square_ratio))

        self.equipped_locs = {
            "ear": Vec3(0, 0, -1),
            "head": Vec3(1/3, 0, -1),
            "neck": Vec3(0, -1/7, -1),
            "chest": Vec3(1/3, -1/7, -1),
            "back": Vec3(2/3, -1/7, -1),
            "legs": Vec3(1/3, -2/7, -1),
            "hands": Vec3(0, -3/7, -1),
            "feet": Vec3(1/3, -3/7, -1),
            "ring": Vec3(2/3, -3/7, -1),
            "mh": Vec3(0, -2/7, -1),
            "oh": Vec3(2/3, -2/7, -1),
            "ammo": Vec3(2/3, 0, -1)
        }
        self.equipped_slots = {
            slot: ItemSlot(text=slot, parent=self.equipped_subframe, origin=(-.5, .5),
                           position=loc * Vec2(1.2, 1.66), scale=(1/3, 1/7), model='quad', color=slot_color)
            for slot, loc in self.equipped_locs.items()
        }

        self.inventory_subframe = Entity(parent=self, origin=(-.5, .5),
                                        position=(edge_margin + 0.45, -edge_margin, -1),
                                        scale=(sq_size * 4, sq_size * 7 * square_ratio))

        self.inventory_locs = [(i / 4, -j / 7, -1) for i in range(4) for j in range(6)]
        self.inventory_slots = [ItemSlot(parent=self.inventory_subframe, origin=(-.5, .5),
                           position=loc, scale=(1/4, 1/7), model='quad', color=slot_color)
                           for loc in self.inventory_locs]

        # Eventually, don't grid whole equipped, just do a 1x1 grid on each slot
        for slot in self.equipped_slots.values():
            grid(slot, num_rows=1, num_cols=1, color=color.black)
        for slot in self.inventory_slots:
            grid(slot, num_rows=1, num_cols=1, color=color.black)

        self.item_icons = []

        self.player = gs.pc.character
        self.make_char_items()

    def make_char_items(self):
        """Reads player inventory and equipment and outputs to UI"""
        for icon in self.item_icons:
            destroy(icon)
        for i, item in enumerate(self.player.inventory):
            if item is not None:
                icon = ItemIcon(item, container=self.player.inventory, slot=i,
                         parent=self.inventory_slots[i], scale=(1, 1), position=(0, 0, -2),
                         origin=(-.5, .5), model='quad', color=color.black)
                self.item_icons.append(icon)
        for i, item in self.player.equipment.items():
            if item is not None:
                icon = ItemIcon(item, container=self.player.equipment, slot=i,
                         parent=self.equipped_slots[i], scale=(1, 1), position=(0, 0, -2),
                         origin=(-.5, .5), model='quad', color=color.black)
                self.item_icons.append(icon)

class ItemSlot(Entity):
    def __init__(self, *args, text="", **kwargs):
        super().__init__(*args, **kwargs)
        if text:
            self.text = Text(text=text, parent=self, origin=(0, 0), position=(0.5, -0.5, -1),
                             world_scale=(11, 11), color=window_fg_color)

class ItemIcon(Entity):
    def __init__(self, item, *args, container=None, slot=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.item = item
        self.container = container
        self.slot = slot

    # def move(self, new_container, new_slot):
    #     pass

    # def on_click(self):
    #     option = self.item['functions'][0]
    #     func = self.item.name_to_func[option]