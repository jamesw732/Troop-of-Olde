from ursina import *

from .base import *
from ..gamestate import gs
from ..item import *

class ItemsWindow(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player = gs.pc.character

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
            slot: ItemSlot(text=slot, container=self.player.equipment, slot=slot,
                           parent=self.equipped_subframe, position=loc * Vec2(1.2, 1.66),
                           scale=(1/3, 1/7), color=slot_color)
            for slot, loc in self.equipped_locs.items()
        }

        self.inventory_subframe = Entity(parent=self, origin=(-.5, .5),
                                        position=(edge_margin + 0.45, -edge_margin, -1),
                                        scale=(sq_size * 4, sq_size * 7 * square_ratio))

        self.inventory_locs = [(i / 4, -j / 7, -1) for i in range(4) for j in range(6)]
        self.inventory_slots = [ItemSlot(container=self.player.inventory, slot=i,
                                         parent=self.inventory_subframe,
                                         position=loc, scale=(1/4, 1/7), color=slot_color)
                                for i, loc in enumerate(self.inventory_locs)]

        # Eventually, don't grid whole equipped, just do a 1x1 grid on each slot
        for slot in self.equipped_slots.values():
            grid(slot, num_rows=1, num_cols=1, color=color.black)
        for slot in self.inventory_slots:
            grid(slot, num_rows=1, num_cols=1, color=color.black)

        self.item_icons = []

        self.make_char_items()

    def make_char_items(self):
        """Reads player inventory and equipment and outputs to UI"""
        for icon in self.item_icons:
            destroy(icon)
        for i, item in enumerate(self.player.inventory):
            if item is not None:
                icon = ItemIcon(item, container=self.player.inventory, slot=i,
                         parent=self.inventory_slots[i], scale=(1, 1), position=(0, 0, -2), color=color.black)
                self.item_icons.append(icon)
        for i, item in self.player.equipment.items():
            if item is not None:
                icon = ItemIcon(item, container=self.player.equipment, slot=i,
                         parent=self.equipped_slots[i], scale=(1, 1), position=(0, 0, -2), color=color.black)
                self.item_icons.append(icon)

    def enable_colliders(self):
        for slot in self.equipped_slots.values():
            slot.collision = True
        for slot in self.inventory_slots:
            slot.collision = True
        for icon in self.item_icons:
            icon.collision = True

    def disable_colliders(self):
        for slot in self.equipped_slots.values():
            slot.collision = False
        for slot in self.inventory_slots:
            slot.collision = False
        for icon in self.item_icons:
            icon.collision = False

class ItemSlot(Entity):
    def __init__(self, *args, text="", container=None, slot=None, **kwargs):
        super().__init__(*args, origin=(-.5, .5), model='quad', collider='box', **kwargs)
        if text:
            self.text = Text(text=text, parent=self, origin=(0, 0), position=(0.5, -0.5, -1),
                             world_scale=(11, 11), color=window_fg_color)
        self.container = container
        self.slot = slot

class ItemIcon(Entity):
    def __init__(self, item, *args, **kwargs):
        super().__init__(*args, origin=(-.5, .5), model='quad', collider='box', **kwargs)
        self.item = item

        self.previous_parent = None
        self.clicked = False
        self.clicked_time = 0
        self.drag_threshold = 0.1
        self.dragging = False
        self.step = Vec3(0, 0, 0)

    def update(self):
        if self.clicked:
            if held_keys["left mouse"]:
                # Wait until we're sure the player is dragging
                if self.clicked_time < self.drag_threshold:
                    self.clicked_time += time.dt
                # When we are sure, start dragging
                elif not self.dragging:
                    self.dragging = True
                    self.collision = False
            else:
                self.clicked_time = 0
                self.clicked = False
                if self.dragging:
                    self.dragging = False
                    new_parent = mouse.hovered_entity
                    if isinstance(new_parent, ItemSlot):
                        self.move(new_parent)
                    self.position = Vec3(0, 0, -1)
                    self.collision = True
            if self.dragging:
                if mouse.position:
                    self.set_position(mouse.position + self.step, camera.ui)


    def move(self, new_parent):
        self.parent = new_parent

    # def on_click(self):
    #     option = self.item['functions'][0]
    #     func = self.item.name_to_func[option]