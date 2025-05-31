from ursina import *

from .base import *
from .window import UIWindow
from ..gamestate import gs

class GameWindow(UIWindow):
    def __init__(self):
        """Window holding relevant game text. Uncertain if this will be in the final product.
        Todo: add handling for having too many messages, and eventually messages that are too long.
        This is likely to turn into a chatbox, and opt for in-game hitsplats to not crowd the messages."""
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
                         scale_x=1, world_scale_y=Text.size*self.font_size[1])
                         # model='quad', color=color.yellow, alpha=1/5)
        self.text_top = Entity(parent=self.textbox, position=(0, -1, -1), origin=(-0.5, -0.5),
                         scale_x=1, world_scale_y=Text.size*self.font_size[1])
                         # model='quad', color=color.yellow, alpha=1/5)


        self.scrollbar = ScrollBar(self, self.textbox, self.text_bottom, self.text_top,
                                   self.text_bottom.world_y, parent=self.body,
                                   origin=(-.5, .5), position=(.925, -.1, -1), scale=(0.05, 0.8),
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
        self.update_text_visibility()
        self.scrollbar.update_scroller_scale_y()

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

    def update_text_visibility(self):
        for msg in self.messages:
            if msg.world_y + Text.size * self.font_size[1] >= self.textbox.world_y \
                    or msg.world_y < self.textbox.world_y - self.textbox.world_scale_y:
                msg.visible = False
            else:
                msg.visible = True

class ScrollBar(Entity):
    def __init__(self, window, frame, bottom_marker, top_marker, bottom_start, **kwargs):
        """General scroll bar class. Could theoretically be used outside of this file

        window: the scope entity which, if hovered, enables scrollwheel scrolling of the scrollbar
        also assumed that window has `update_text_visibility`, eventually this should be a shader
        frame: the entity defining the area of the content we care about
        bottom_marker: entity defining the variable bottom of the block to scroll over
        top_marker: entity defining the variable top of the block to scroll over
        bottom_start: y value of the initial posiiton of bottom_marker"""
        super().__init__(**kwargs)
        gs.ui.colliders.append(self)
        self.window = window
        self.frame = frame
        self.bottom_marker = bottom_marker
        self.top_marker = top_marker
        self.bottom_start = bottom_start
        scroller_scale_y = self.get_scroller_scale_y()
        self.scroller = Entity(parent=self, origin=(-0.5, -0.5), scale=(1, scroller_scale_y), position=(0, -1),
                               model='quad', color=color.gray)
        self.drag_sequence = Sequence(Func(self.match_mouse), loop=True)

    def get_scroller_scale_y(self):
        if self.top_marker.world_y == self.bottom_marker.world_y:
            return 1
        return min(1, self.frame.world_scale_y / (self.top_marker.world_y - self.bottom_marker.world_y))

    def update_scroller_scale_y(self):
        self.scroller.scale_y = self.get_scroller_scale_y()

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
        self.match_markers_to_scrollbar()

    def scroll_up(self):
        self.scroller.y = clamp(self.scroller.y + 0.05, -1, -self.scroller.scale_y)
        self.match_markers_to_scrollbar()

    def scroll_down(self):
        self.scroller.y = clamp(self.scroller.y - 0.05, -1, -self.scroller.scale_y)
        self.match_markers_to_scrollbar()

    def match_markers_to_scrollbar(self):
        min_scroll_y = -1
        max_scroll_y = -self.scroller.scale_y
        scrollbar_ratio = (self.scroller.y - min_scroll_y) / (max_scroll_y - min_scroll_y)
        dist = self.top_marker.world_y - self.bottom_marker.world_y
        self.bottom_marker.world_y = self.bottom_start - dist * scrollbar_ratio
        self.top_marker.world_y = self.bottom_marker.world_y + dist
        self.window.update_text_visibility()
