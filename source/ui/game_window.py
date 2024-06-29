from ursina import *

from .base import *
from .header import *

class GameWindow(Entity):
    def __init__(self):
        header = Header(
            position=(-0.87, -0.25, 0),
            scale=(0.35, 0.033),
            color=header_color,
            text="Game",
            ignore_key = lambda c: isinstance(c, Text)
        )

        super().__init__(
            parent=header, model='quad', origin=(-.5, .5),
            position=(0, -1, 0), scale=(1, 6),
            color=window_bg_color,
            collider='box'
        )
        self.scrollbar = ScrollBar(parent=self, scale=(0.05, 0.2), position=(0.925, -0.1, -1))

class ScrollBar(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, model='quad', collider='box',
                         origin=(-.5, .5), color=color.gray, **kwargs)
        self.max_y = -0.1
        self.min_y = -0.9 + self.scale_y
        self.y = self.min_y
        self.global_parent = self.parent.parent
        # The offset between mouse position and origin of scrollbar position
        self.step = 0
        self.dragging = False
        self.parents = get_ui_parents([self])

    def input(self, key):
        if self.hovered and key == "left mouse down":
            self.dragging = True
            self.step = get_global_y(self.y, self) - mouse.y
        elif self.dragging and key == "left mouse up":
            self.dragging = False
    
    def update(self):
        if self.dragging:
            if mouse.position:
                global_max_y = get_global_y(self.max_y, self)
                global_min_y = get_global_y(self.min_y, self)
                y = mouse.y + self.step
                self.y = get_local_y(clamp(y, global_min_y, global_max_y), self.parents)