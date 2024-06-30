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
        self.scrollbar_box = Entity(parent=self, origin=(-.5, .5),
                                    position=(.925, -.1, -1), scale=(0.05, 0.8),
                                    collider='box')
        grid(self.scrollbar_box, num_rows=1, num_cols=1, color=color.gray)
        self.scrollbar = ScrollBar(parent=self.scrollbar_box, scale=(1, 0.25), position=(0, 0, -2))

        self.font_size = Vec2(11, 11)
        self.text_height = 0.4 # Magic number, real scale is 0.55 but includes padding
        self.messages = []

        self.textcontainer = Entity(parent=self, origin=(-.5, .5),
                                    position=(.025, -.05, -1), scale=(.875, .9))
        grid(self.textcontainer, num_rows=1, num_cols=1, color=color.gray)
        # Remove these magic numbers for position and scale
        self.text_bottom = Entity(parent=self.textcontainer, origin=(-.5, .5),
                                  position=(0.01, -.86, -2), scale_x=0.99,
                                  world_scale_y=self.text_height)
        self.text_top = Entity(parent=self.textcontainer, origin=(-.5, .5),
                               position=self.text_bottom.position, scale=self.text_bottom.scale)
        # Top/bottom demarkers which are variant under adding messages, but invariant under scrolling
        self.bottom_y = self.text_bottom.world_y
        self.top_y = self.text_top.world_y

        self.max_lines = 100
        self.min_visible = 0
        self.max_visible = self.max_lines * self.text_height

    def update(self):
        if self.scrollbar.dragging:
            min_scroll_y = -1 + self.scrollbar.scale_y
            max_scroll_y = 0
            scrollbar_ratio = (min_scroll_y - self.scrollbar.y) / (max_scroll_y - min_scroll_y)
            offset = scrollbar_ratio * (self.max_visible - self.min_visible)
            self.text_bottom.world_y = self.bottom_y + offset
            self.text_top.world_y = self.top_y + offset

    def add_message(self, msg):
        # Remove word wrap magic number
        msg = WindowText(self.textcontainer, self.text_height, text=msg, parent=self.text_top,
                         origin=(-.5, -.5), world_scale=self.font_size, color=text_color,
                         wordwrap=45)
        self.text_top.world_y += self.text_height * len(msg.txt.lines)
        self.top_y += self.text_height * len(msg.txt.lines)
        msg.txt.world_position = self.text_bottom.world_position - Vec2(0, self.text_height)
        self.messages.append(msg)
        if len(self.messages) > self.max_lines: # Imprecise, but whatever
            destroy(self.messages[0])
            self.messages.pop(0)

class ScrollBar(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, model='quad', collider='box',
                         origin=(-.5, .5), color=color.gray, **kwargs)
        self.max_y = 0
        self.min_y = -1 + self.scale_y
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

class WindowText(Entity):
    def __init__(self, box, textheight, *args, **kwargs):
        super().__init__()
        self.txt = Text(*args, **kwargs)
        self.box = box
        self._height = textheight * len(self.txt.lines)

    def update(self):
        max_y = self.box.world_y
        min_y = self.box.world_y - self.box.world_scale_y
        # Text origin is bottom left
        show = (self.txt.world_y + self._height < max_y) and (self.txt.world_y > min_y)
        if self.txt.visible and not show:
            self.txt.visible = False
        elif not self.txt.visible and show:
            self.txt.visible = True

    def on_destroy(self):
        destroy(self.txt)