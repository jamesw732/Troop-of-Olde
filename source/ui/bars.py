from ursina import *

from .base import *
from .header import *

from ..gamestate import gs

class BarWindow(Entity):
    def __init__(self):
        self.player = gs.pc.character
        header = Header(
            position=window.top_left,
            scale=(.2, .033),
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

        self.bar_height = 1/3

        self.healthbar = Entity(
            parent=self.bar_bg, model='quad', origin=(-.5, .5),
            position=(0, 0, -2), scale=(1, self.bar_height),
            color=color.red
        )
        self.manabar = Entity(
            parent=self.bar_bg, model='quad', origin=(-.5, .5),
            position=(0, -self.bar_height, -2),
            scale=(1, self.bar_height),
            color=color.hex("0000cc")
        )
        self.stambar = Entity(
            parent=self.bar_bg, model='quad', origin=(-.5, .5),
            position=(0, -2 * (self.bar_height), -2),
            scale=(1, self.bar_height),
            color=color.yellow
        )

        grid(self.bar_bg, num_rows=3, num_cols=1, color=color.black)

        self.update_rate = 1.0
        self.update_timer = 0.0

    def update(self):
        self.update_timer += time.dt
        if self.update_timer > self.update_rate:
            self.update_timer -= self.update_rate
            self.update_health()
            self.update_mana()
            self.update_stamina()

    def update_health(self):
        ratio = self.player.health / self.player.maxhealth
        self.healthbar.scale = (ratio, self.bar_height)

    def update_mana(self):
        ratio = self.player.mana / self.player.maxmana
        self.manabar.scale = (ratio, self.bar_height)

    def update_stamina(self):
        ratio = self.player.stamina / self.player.maxstamina
        self.stambar = (ratio, self.bar_height)