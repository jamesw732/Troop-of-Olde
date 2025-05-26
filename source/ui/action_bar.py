from ursina import *

from .base import *
from ..gamestate import gs
from .window import UIWindow


class ActionBar(UIWindow):
    def __init__(self):
        self.num_slots = gs.pc.num_powers
        self.total_slot_width = 0.5
        self.slot_height = self.total_slot_width / self.num_slots

        header_ratio = 1 / 7
        self.header_height = self.slot_height * header_ratio

        margin_ratio = 1 / 10
        self.margin = self.slot_height * margin_ratio

        self.total_width = 2 * self.margin + self.total_slot_width
        self.total_height = 2 * self.margin + self.slot_height + self.header_height

        start_pos = (-self.total_width / 2, -0.5 + self.total_height + self.header_height)
        super().__init__(header_ratio=header_ratio, scale=(self.total_width, self.total_height),
                         position=start_pos, bg_alpha=1)

        # Initialize the actual bar that holds the powers.
        pbar_world_pos = camera.ui.scale * Vec3(self.margin, -self.header_height - self.margin, -1) \
                + self.world_position
        pbar_world_scale = camera.ui.scale * Vec3(self.total_slot_width, self.slot_height, 1)
        self.powerbar = PowerBar(parent=self, world_position=pbar_world_pos, origin=(-0.5, 0.5),
                               world_scale=pbar_world_scale,
                               color=window_fg_color, model='quad')
        
        grid(self.powerbar, 1, 10, color=color.black)

    def start_gcd_animation(self):
        for i, icon in enumerate(self.powerbar.power_icons):
            if icon is None:
                continue
            icon.gcd_overlay = Timer(parent=self.powerbar, origin=(-.5, .5),
                                     position=(i / self.num_slots, 0, -5), 
                                     model='quad', color=color.gray, alpha=0.6,
                                     scale_x = (1 - gs.pc.gcd_timer / gs.pc.gcd) / self.num_slots)


class PowerBar(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.power_icons = [None] * self.parent.num_slots
        self.labels = []
        outlines = []
        for i, power in enumerate(gs.pc.powers):
            if power is not None:
                self.power_icons[i] = Entity(parent=self, origin=(-0.5, 0.5),
                                             scale=(1 / self.parent.num_slots, 1), 
                                             position=(i / self.parent.num_slots, 0, -1),
                                             model='quad', texture=power.icon)
            label = str(i + 1)
            self.labels.append(Text(text=label, parent=self, world_scale=(12, 12),
                                         position=((i + 0.05) / self.parent.num_slots, -.95, -2),
                                    origin=(-0.5, -0.5), color=color.white))
            cur_outlines = []
            offset_amt = 0.00263
            for offset in [(offset_amt, 0), (offset_amt, offset_amt), (0, offset_amt),
                           (-offset_amt, offset_amt), (-offset_amt, 0), (-offset_amt, -offset_amt),
                           (0, -offset_amt), (offset_amt, -offset_amt)]:
                cur_outlines.append(Text(text=label, parent=self.labels[i], position=(*offset, 0.9),
                                         origin=(-0.5, -0.5), world_scale=(12, 12), color=color.black))

        
        self.key_to_slot = {f"power_{i + 1}": i for i in range(self.parent.num_slots)}

    def input(self, key):
        if key not in self.key_to_slot:
            return
        slot = self.key_to_slot[key]
        power = gs.pc.powers[slot]
        if power is None:
            return
        power.handle_power_input()

class Timer(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update(self):
        self.scale_x = (1 - gs.pc.gcd_timer / gs.pc.gcd) / gs.pc.num_powers
        if self.scale_x <= 0:
            destroy(self)
            self.parent.gcd_overlay = None
