from ursina import *

from .base import *
from .window import UIWindow

class GameWindow(UIWindow):
    def __init__(self):
        scale = (0.35, 0.25)
        super().__init__(position=(-0.495 * window.aspect_ratio, -0.49 + scale[1]), scale=scale, bg_alpha=200/255)
        self.font_size = Vec2(11, 11)
        self.messages = []
        self.char_widths = {}

        # The box containing the text visually
        self.textbox = Entity(parent=self.body, origin=(-.5, .5),
                                    position=(.025, -.05, -1), scale=(.875, .9))
        grid(self.textbox, num_rows=1, num_cols=1, color=color.gray)
        # The invisible Entity containing the Text
        self.text_bottom = Entity(parent=self.textbox, position=(0, -1, -1), origin=(-0.5, -0.5),
                         scale_x=1, world_scale_y=Text.size*self.font_size[1],
                         model='quad', color=color.yellow, alpha=1/5)
        self.text_top = Entity(parent=self.textbox, position=(0, -1, -1), origin=(-0.5, -0.5),
                         scale_x=1, world_scale_y=Text.size*self.font_size[1],
                         model='quad', color=color.yellow, alpha=1/5)


        self.scrollbar = ScrollBar(self, parent=self.body, origin=(-.5, .5),
                                    position=(.925, -.1, -1), scale=(0.05, 0.8),
                                    collider='box', model='quad', alpha=0)
        self.scrollbar.ignore_focus = True

        grid(self.scrollbar, num_rows=1, num_cols=1, color=color.gray)

    def add_message(self, msg):
        wordwrap = self.get_word_wrap(msg, self.textbox.world_scale_x)
        # wordwrap = 45
        # This has the potential to be buggy if there's a single word with length equal to wordwrap minus 1
        # The reason we add 1 inside is because wordwrap internally calculates the length as the sum
        # of all cleaned words plus 1 for the space, but this overcounts the spaces by 1
        num_lines = int((len(msg) + 1) // wordwrap) + 1
        shift_amt = Text.size * self.font_size[1] * num_lines
        self.text_top.world_y += shift_amt
        self.messages.append(Text(text=msg, parent=self.text_top, world_scale=self.font_size,
                                  world_position=self.text_bottom.world_position, origin=(-0.5, -0.5),
                                  color=text_color, wordwrap=wordwrap))


    def get_word_wrap(self, txt, max_width):
        cur_width = 0
        i = 0
        word_wraps = []
        for c in txt:
            if c in self.char_widths:
                cur_width += self.char_widths[c]
            else:
                width = Text.get_width(c) * self.font_size[0]
                self.char_widths[c] = width
                cur_width += width
            if cur_width > max_width:
                word_wraps.append(i - 1)
                i = 0
                cur_width = 0
            else:
                i += 1
        if len(word_wraps) > 0:
            return min(word_wraps)
        return len(txt) + 2


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

