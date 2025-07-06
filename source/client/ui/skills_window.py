from ursina import *

from .base import *
from ... import all_skills, gs

class SkillsWindow(Entity):
    def __init__(self, *args, **kwargs):
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
        self.write_skills()

    def write_skills(self):
        for i, skill in enumerate(all_skills):
            position = (self.edge_margin, -self.edge_margin - (self.vertical_spacing + self.text_height) * i, -1)
            self.create_label(skill, position)

    def create_label(self, skill, position):
        fmt = (f"{skill}", "{}")
        txt = self.format_text(fmt, gs.pc.skills[skill])
        self.labels[skill] = Text(parent=self, origin=(-.5, .5),
             world_scale=self.text_size, position=position,
             text=txt, color=color.white, font='VeraMono.ttf')
        self.labels[skill].fmt = fmt

    def format_text(self, fmt, *args):
        first_part = fmt[0]
        second_part = fmt[1].format(*args)
        length = len(first_part) + len(second_part)
        pad = ' ' * (self.max_chars - length)
        return pad.join([first_part, second_part])

    def set_label_text(self, skill):
        label = self.labels[skill]
        fmt = label.fmt
        txt = self.format_text(fmt, gs.pc.skills[skill])
        label.text = txt

    def enable_colliders(self):
        pass

    def disable_colliders(self):
        pass