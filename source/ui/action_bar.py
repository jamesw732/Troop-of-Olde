from ursina import *

from .base import *
from .window import UIWindow


class ActionBar(UIWindow):
    def __init__(self):
        self.num_slots = 10
        total_slot_width = 0.5
        slot_height = total_slot_width / self.num_slots

        header_ratio = 1 / 7
        header_height = slot_height * header_ratio

        margin_ratio = 1 / 10
        margin = slot_height * margin_ratio

        total_width = 2 * margin + total_slot_width
        total_height = 2 * margin + slot_height + header_height

        # start_pos = Vec2(window.aspect_ratio / 2 - total_width / 2, -0.9)
        start_pos = (-total_width / 2, -0.5 + total_height + header_height)
        # start_pos = (0, -0.415)
        super().__init__(header_ratio=header_ratio, scale=(total_width, total_height), position=start_pos,
                         bg_alpha=1)

        # Initialize the actual bar that holds the powers.
        pbar_world_pos = camera.ui.scale * Vec3(margin, -header_height - margin, -1) + self.world_position
        pbar_world_scale = camera.ui.scale * Vec3(total_slot_width, slot_height, 1)
        self.powerbar = Entity(parent=self, world_position=pbar_world_pos, origin=(-0.5, 0.5),
                               world_scale=pbar_world_scale,
                               color=window_fg_color, model='quad')
        
        grid(self.powerbar, 1, 10, color=color.black)
