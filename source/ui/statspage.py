from ursina import *

from .draggable_header import *
from ..gamestate import gs

class StatsPage(Entity):
    def __init__(self):
        header = DraggableHeader(position=(0.2, 0.2),
                                 scale=(.5, .03),
                                 color=color.rgb32(115, 85, 57))
        super().__init__(parent=header, model='quad', origin=(-.5, .5),
                         position=(0, -1), scale=(1, 16),
                         color=color.rgb32(0, 100, 0),
                         collider='box')

        self.parent.visible = False

    def update(self):
        if self.hovered or self.parent.hovered:
            self.alpha = 1
            self.parent.alpha = 1
        else:
            self.alpha = 200 / 255
            self.parent.alpha = 200 / 255

    def input(self, key):
        if key == "open stats":
            self.parent.visible = not self.parent.visible