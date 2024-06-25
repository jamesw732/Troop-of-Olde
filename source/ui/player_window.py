from ursina import *

from .base import *
from .header import *
from .stats_window import *

from ..gamestate import gs

class PlayerWindow(Entity):
    def __init__(self):
        self.player = gs.pc.character
        header = Header(
            position=(0.2, 0.2),
            scale=(.44, .033),
            color=header_color,
            text=self.player.cname
        )
        super().__init__(
            parent=header, model='quad', origin=(-.5, .5),
            position=(0, -1), scale=(1, 12),
            color=window_bg_color,
            collider='box'
        )

        self.stats = StatsWindow(parent=self, model='quad', origin=(-.5, .5),
                                 scale=(.8, .8), position=(.1, -.1, -1),
                                 color=window_fg_color)

        self.parent.visible = False

    def write_stats(self):
        pass

