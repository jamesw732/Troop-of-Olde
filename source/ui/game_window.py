from ursina import *

from .base import *
from .window import UIWindow

class GameWindow(UIWindow):
    def __init__(self):
        super().__init__(position=(-0.495 * window.aspect_ratio, -0.29), scale=(0.3, 0.2), bg_alpha=200/255)

        self.scrollbar = ScrollBar(self, parent=self.body, origin=(-.5, .5),
                                    position=(.925, -.1, -1), scale=(0.05, 0.8),
                                    collider='box', model='quad', alpha=0)
        self.scrollbar.ignore_focus = True

        grid(self.scrollbar, num_rows=1, num_cols=1, color=color.gray)

        self.font_size = Vec2(11, 11)
        self.messages = []

        self.textcontainer = Entity(parent=self.body, origin=(-.5, .5),
                                    position=(.025, -.05, -1), scale=(.875, .9))
        grid(self.textcontainer, num_rows=1, num_cols=1, color=color.gray)



class ScrollBar(Entity):
    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.window = window
        self.scroller = Entity(parent=self, origin=(-0.5, -0.5), scale=(1, 0.25), position=(0, -1),
                               model='quad', color=color.gray)
        self.drag_sequence = Sequence(Func(self.match_mouse), loop=True)


    def input(self, key):
        tgt = mouse.hovered_entity
        if tgt is None or tgt not in (self, self.window):
            return
        if tgt is self:
            if key == "left mouse down":
                self.drag_sequence.start()
        if key == "left mouse up":
            self.drag_sequence.finish()
        if key == "scroll up":
            self.scroll_up()
        elif key == "scroll down":
            self.scroll_down()

    def match_mouse(self):
        self.scroller.world_y = mouse.y * camera.ui.scale_y - self.scroller.world_scale_y / 2
        self.scroller.y = clamp(self.scroller.y, -1, -self.scroller.scale_y)

    def scroll_up(self):
        self.scroller.y = clamp(self.scroller.y + 0.05, -1, -self.scroller.scale_y)

    def scroll_down(self):
        self.scroller.y = clamp(self.scroller.y - 0.05, -1, -self.scroller.scale_y)

