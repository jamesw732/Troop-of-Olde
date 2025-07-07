from ursina import *
import itertools

from .base import *
from ... import all_stats

class StatsWindow(Entity):
    def __init__(self, char, *args, **kwargs):
        self.char = char
        super().__init__(*args, **kwargs)
        self.text_size = Vec2(12, 12)
        # Absolute text width
        text_width = Text.get_width(' ', font='VeraMono.ttf') * self.text_size[0]
        # Relative text height
        self.text_height = Text.size * self.text_size[1] / self.world_scale_y

        self.edge_margin = 0.02
        self.vertical_spacing = 0.01

        self.max_chars = int(self.world_scale_x / text_width * (1 - 2 * self.edge_margin))

        self.labels = {}
        self.labels_with_max = ["health", "energy"]
        self.write_stats()

    def write_stats(self):
        for i, stat in enumerate(all_stats):
            position = (self.edge_margin, -self.edge_margin - (self.vertical_spacing + self.text_height) * i, -1)
            self.create_label(stat, position)

    def create_label(self, stat, position):
        if stat in self.labels_with_max:
            fmt = (f"{stat}", "{}/{}")
            txt = self.format_text(fmt, getattr(self.char, stat), getattr(self.char, "max" + stat))
        else:
            fmt = (f"{stat}", "{}")
            txt = self.format_text(fmt, getattr(self.char, stat))
        self.labels[stat] = Text(parent=self, origin=(-.5, .5),
             world_scale=self.text_size, position=position,
             text=txt, color=color.white, font='VeraMono.ttf')
        self.labels[stat].fmt = fmt

    def format_text(self, fmt, *args):
        first_part = fmt[0]
        second_part = fmt[1].format(*args)
        length = len(first_part) + len(second_part)
        pad = ' ' * (self.max_chars - length)
        return pad.join([first_part, second_part])

    def update_labels(self):
        for attr in self.labels:
            self.update_label(attr)

    def update_label(self, attr):
        label = self.labels[attr]
        fmt = label.fmt
        cur = getattr(self.char, attr)
        if attr in self.labels_with_max:
            cap = getattr(self.char, "max" + attr)
            txt = self.format_text(fmt, cur, cap)
        else:
            txt = self.format_text(fmt, cur)
        label.text = txt


    def enable_colliders(self):
        pass

    def disable_colliders(self):
        pass