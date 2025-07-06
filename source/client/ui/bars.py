from ursina import *

from .base import *
from .window import UIWindow

from ... import gs

class BarWindow(UIWindow):
    def __init__(self):
        self.player = gs.pc
        # super().__init__(position=(0, -1, 0), scale=(1, 2.5))
        super().__init__(position=(-0.495 * window.aspect_ratio, 0.49), scale=(0.2, 0.08), bg_alpha=220/255)

        self.bar_bg = Entity(
            parent=self.body, model='quad', origin=(-.5, .5),
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
        self.healthbar.ignore_focus = True
        self.energybar.ignore_focus = True

        grid(self.bar_bg, num_rows=2, num_cols=1, color=color.black)

        self.update_display()

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