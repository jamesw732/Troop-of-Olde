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
        self.messages = []

        self.textcontainer = Entity(parent=self, origin=(-.5, .5),
                                    position=(.025, -.05, -1), scale=(.875, .9))
        grid(self.textcontainer, num_rows=1, num_cols=1, color=color.gray)
        # Remove these magic numbers for position and scale
        self.text_bottom = Entity(parent=self.textcontainer, origin=(-.5, .5),
                                  position=(0, -.86, -2), scale=(1, 0.12),
                                 )

    def add_message(self, msg):
        txt = Text(text=msg, parent=self.text_bottom, origin=(-.5, -.5),
             position=(0.01, -1, -3), world_scale=self.font_size,
             color=text_color, wordwrap=45) # Remove word wrap magic number
        for msg in self.messages:
            msg.y += len(txt.lines)
        self.messages.append(txt)
        if len(self.messages) > 50:
            destroy(self.messages[0])
            self.messages.pop(0)

# self.text_top = Entity(parent=self.textcontainer, origin=(-.5, .5),
#                                position=(0, -.88, -2), scale_x=1, world_scale_y=self.font_size[1],
#                                model='quad')

#     def add_message(self, msg):
#         txt = Text(text=msg, parent=self.text_top, origin=(-.5, -.5),
#              x=0, world_y=self.text_bottom.world_y, world_scale=self.font_size,         # Remove this magic number
#              color=text_color, wordwrap=45) # Remove this magic number too
#         self.text_top.y += txt.scale_y
#         # for msg in self.messages:
#         #     msg.y += txt.height
#         self.messages.append(txt)
#         if len(self.messages) > 50:
#             destroy(self.messages[0])
#             self.messages.pop(0)

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