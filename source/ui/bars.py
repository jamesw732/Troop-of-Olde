from ursina import *

from .base import *
from .header import *

from ..gamestate import gs

class BarWindow(Entity):
    def __init__(self):
        self.player = gs.pc
        header = Header(
            position=window.top_left,
            scale=(.2, .02),
            color=header_color,
            ignore_key=lambda c: True
        )
        super().__init__(
            parent=header, model='quad', origin=(-.5, .5),
            position=(0, -1, 0), scale=(1, 2.5),
            color=window_bg_color,
            collider='box'
        )
        header.set_ui_scale(self)

        self.bar_bg = Entity(
            parent=self, model='quad', origin=(-.5, .5),
            position=(0.05, -0.05, -1), scale=(0.9, 0.9),
            color=window_bg_color)

        self.bar_height = 1/2

        self.healthbar = Entity(
            parent=self.bar_bg, model='quad', origin=(-.5, .5),
            position=(0, 0, -2), scale=(1, self.bar_height),
            color=color.red
        )
        self.energybar = Entity(
            parent=self.bar_bg, model='quad', origin=(-.5, .5),
            position=(0, -self.bar_height, -2),
            scale=(1, self.bar_height),
            color=color.hex("00cc00")
        )

        grid(self.bar_bg, num_rows=2, num_cols=1, color=color.black)

        self.update_rate = 1.0
        self.update_timer = 0.0

    def update_display(self):
        self.update_health()
        self.update_energy()

    def update_health(self):
        if self.player.maxhealth == 0:
            ratio = 0
        else:
            ratio = self.player.health / self.player.maxhealth
        self.healthbar.scale = (ratio, self.bar_height)

    def update_energy(self):
        if self.player.maxenergy == 0:
            ratio = 0
        else:
            ratio = self.player.energy / self.player.maxenergy
        self.energybar.scale = (ratio, self.bar_height)