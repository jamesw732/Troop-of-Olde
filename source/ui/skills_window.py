from ursina import *

from .base import *
from .. import all_skills
from .header import *
from ..gamestate import gs

class SkillsWindow(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_size = Vec2(12, 12)
        # Text size relative to camera.ui
        tw_abs = self.text_size[0] * Text.size * .61
        th_abs = self.text_size[1] * Text.size
        # Text height relative to frame
        tw_rel = tw_abs / self.world_scale_x / 0.46
        th_rel = th_abs / self.world_scale_y

        self.subheader_size = Vec2(18, 18)
        # subheader height relative to frame
        self.subheader_h = 1.5 * th_rel
        # Max number of characters
        self.max_chars = int(1 / tw_rel)
        # Amount to separate each line of text
        self.step = 1.1 * th_rel

        self.labels = {}

        self.wep_style_skills = [
            "1h melee",
            "2h melee",
            "fists",
        ]
        self.off_skills = [
            "critical hit",
            "flurry",
            "dual wield"
        ]
        self.def_skills = [
            "parry",
            "dodge",
            "shields",
            "riposte",
        ]
        self.cast_skills = [
            "enchantment",
            "curse",
            "necromancy",
            "transformation",
        ]

        self.write_wep_styles()
        self.write_off_skills()
        self.write_def_skills()
        self.write_cast_skills()

    def format_text(self, fmt, *args):
        first_part = fmt[0]
        second_part = fmt[1].format(*args)
        length = len(first_part) + len(second_part)
        pad = ' ' * (self.max_chars - length)
        return pad.join([first_part, second_part])

    def create_label(self, skill, position):
        fmt = (f"{skill}", "{}")
        txt = self.format_text(fmt, gs.pc.skills[skill])
        self.labels[skill] = Text(parent=self, origin=(-.5, .5),
             world_scale=self.text_size, position=position,
             text=txt, color=color.white, font='VeraMono.ttf')
        self.labels[skill].fmt = fmt

    def write_wep_styles(self):
        Text(text='Weapon Styles', parent=self, origin=(0, 0), world_scale=self.subheader_size,
             position=(0.25, -self.subheader_h, -1))
        offset = -0.02 - self.subheader_h * 1.5
        for i, skill in enumerate(self.wep_style_skills):
            position = (0.02, offset - self.step * i, -1)
            self.create_label(skill, position)

    def write_cast_skills(self):
        header_h = -0.02 - 2.5 * self.subheader_h - self.step * len(self.wep_style_skills)
        Text(text='Casting Skills', parent=self, origin=(0, 0), world_scale=self.subheader_size,
             position=(0.25, header_h, -1))
        offset = -0.02 + header_h - self.subheader_h * 0.5
        for i, skill in enumerate(self.cast_skills):
            position = (0.02, offset - self.step * i, -1)
            self.create_label(skill, position)

    def write_off_skills(self):
        Text(text='Offensive Skills', parent=self, origin=(0, 0), world_scale=self.subheader_size,
             position=(0.75, -self.subheader_h, -1))
        offset = -0.02 - self.subheader_h * 1.5
        for i, skill in enumerate(self.off_skills):
            position = (0.52, offset - self.step * i, -1)
            self.create_label(skill, position)

    def write_def_skills(self):
        header_h = -0.02 - 2.5 * self.subheader_h - self.step * len(self.off_skills)
        Text(text='Defensive Skills', parent=self, origin=(0, 0), world_scale=self.subheader_size,
             position=(0.75, header_h, -1))
        offset = -0.02 + header_h - self.subheader_h * 0.5
        for i, skill in enumerate(self.def_skills):
            position = (0.52, offset - self.step * i, -1)
            self.create_label(skill, position)

    def set_label_text(self, skill):
        label = self.labels[skill]
        fmt = label.fmt
        txt = self.format_text(fmt, gs.pc.skills[skill])
        label.text = txt

    def enable_colliders(self):
        pass

    def disable_colliders(self):
        pass