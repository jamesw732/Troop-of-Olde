from ursina import *

from .base import *
from .items import ItemFrame
from ... import *

"""Explanation of terminology used in this file:
ItemsWindow is the PlayerWindow subframe, the highest ancestor in this file
ItemFrame represents a grid of items, and handles most of the items UI inputs
"""


class ItemsWindow(Entity):
    def __init__(self, char, items_manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This is used to normalize lengths relative to the width/height of the ItemsWindow
        # Given a width/length, multiply the length by window_wh_ratio to get the correct
        # length relative to the width
        window_wh_ratio = self.world_scale_x / self.world_scale_y
        # How far away from the edge to put the subcontainers
        edge_margin = 0.025

        # Make equipment subframe
        equip_frame_width = 0.4
        equip_grid_size = Vec2(2, 2)
        equip_box_spacing = 0

        equip_frame_height = get_grid_height(
            equip_frame_width, equip_grid_size, spacing=equip_box_spacing,
            window_wh_ratio=window_wh_ratio
        )
        equip_frame_scale = Vec3(equip_frame_width, equip_frame_height, 1)
        equip_frame_pos = ((1 - equip_frame_width) / 2, equip_frame_height + edge_margin - 1, -1)

        self.equipment_frame = items_manager.make_item_frame(
            equip_grid_size, char.equipment,
            slot_labels=equipment_slots,
            parent=self, position=equip_frame_pos,
            scale=equip_frame_scale
        )

        # Make inventory subframe
        inventory_frame_width = 1 - 8 * edge_margin
        inventory_grid_size = (4, 5)
        inventory_box_spacing = 0

        inventory_frame_height = get_grid_height(
            inventory_frame_width, inventory_grid_size,
            spacing=inventory_box_spacing, window_wh_ratio=window_wh_ratio
        )
        inventory_position = (4 * edge_margin, -edge_margin, -1)
        inventory_frame_scale = Vec2(inventory_frame_width, inventory_frame_height)

        self.inventory_frame = items_manager.make_item_frame(
            inventory_grid_size, char.inventory,
            parent=self, position=inventory_position, scale=inventory_frame_scale
        )

    def enable_colliders(self):
        self.inventory_frame.collision = True
        self.equipment_frame.collision = True

    def disable_colliders(self):
        self.inventory_frame.collision = False
        self.equipment_frame.collision = False
