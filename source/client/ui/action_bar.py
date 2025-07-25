from ursina import *

from .base import *
from .window import UIWindow
from ... import power_key_to_slot, default_num_powers


class ActionBar(UIWindow):
    def __init__(self, char, ctrl):
        self.char = char
        self.ctrl = ctrl
        self.num_slots = default_num_powers
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
        self.powerbar = PowerBar(char, ctrl, parent=self, world_position=pbar_world_pos,
                                 origin=(-0.5, 0.5), world_scale=pbar_world_scale, collider='box',
                               color=window_fg_color, model='quad')
        
        grid(self.powerbar, 1, 10, color=color.black)

    def start_cd_animation(self):
        for i, icon in enumerate(self.powerbar.power_icons):
            if icon is None or icon.cd_overlay is not None:
                continue
            icon.cd_overlay = Timer(self.char, self.char.powers[i], parent=icon, origin=(-.5, .5),
                                     position=(0, 0, -5), 
                                     model='quad', color=color.gray, alpha=0.6,
                                     scale_x = 1)


class PowerBar(Entity):
    def __init__(self, char, ctrl, **kwargs):
        self.char = char
        self.ctrl = ctrl
        super().__init__(**kwargs)
        self.power_icons = [None] * self.parent.num_slots
        self.labels = []
        outlines = []
        for i, power in enumerate(self.char.powers):
            if power is not None:
                self.power_icons[i] = Entity(parent=self, origin=(-0.5, 0.5),
                                             scale=(1 / self.parent.num_slots, 1), 
                                             position=(i / self.parent.num_slots, 0, -1),
                                             model='quad', texture=power.icon)
                self.power_icons[i].cd_overlay = None
            label = str(i + 1)
            self.labels.append(Text(text=label, parent=self, world_scale=(12, 12),
                                         position=((i + 0.05) / self.parent.num_slots, -.95, -2),
                                    origin=(-0.5, -0.5), color=color.white))
            cur_outlines = []
            # This is a magic number that was found experimentally to minimze blur.
            # Might depend on resolution of monitor and aspect ratio of the window.
            offset_amt = 0.00263
            for offset in [(offset_amt, 0), (offset_amt, offset_amt), (0, offset_amt),
                           (-offset_amt, offset_amt), (-offset_amt, 0), (-offset_amt, -offset_amt),
                           (0, -offset_amt), (offset_amt, -offset_amt)]:
                cur_outlines.append(Text(text=label, parent=self.labels[i], position=(*offset, 0.9),
                                         origin=(-0.5, -0.5), world_scale=(12, 12), color=color.black))

    def handle_power_input(self, key):
        slot = power_key_to_slot[key]
        power = self.char.powers[slot]
        if power is None:
            return
        self.ctrl.handle_power_input(power)

    def on_click(self):
        ui_mouse_x = mouse.x * camera.ui.scale_x
        rel_mouse_x = ui_mouse_x - self.world_x
        slot_world_scale_x = self.world_scale_x / self.parent.num_slots
        slot = int(rel_mouse_x // slot_world_scale_x)

        power = self.char.powers[slot]
        if power is None:
            return
        self.ctrl.handle_power_input(power)


class Timer(Entity):
    def __init__(self, char, power, *args, **kwargs):
        self.char = char
        self.power = power
        super().__init__(*args, **kwargs)
        self.ignore_focus = True

    def update(self):
        self.alpha = 0.6
        # Choose gcd or individual cd timer, whichever will finish later
        if self.char.gcd - self.char.gcd_timer >= self.power.cooldown - self.power.timer:
            self.scale_x = 1 - self.char.gcd_timer / self.char.gcd
        else:
            self.scale_x = 1 - self.power.timer / self.power.cooldown
        if self.scale_x <= 0:
            destroy(self)
            self.parent.cd_overlay = None
