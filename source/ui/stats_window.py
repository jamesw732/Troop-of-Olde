from ursina import *
import itertools

from .base import *
from .header import *
from ..gamestate import gs

class StatsWindow(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player = gs.pc.character
        self.header = self.parent.parent

        self.num_rows = 14
        self.num_cols = 2
        self.row_width = 1 / self.num_rows
        self.col_width = 1 / self.num_cols

        self.entries = {}
        self.entry_font_size = (11, 11)
        self.entry_width = 19

        # grid(self, 14, 2)

        self.labels_out_of_max = {"health", "mana", "stamina", "spellshield"}

        self.rating_labels = [
            ('health', 'Health'),
            ('mana', 'Mana'),
            ('stamina', 'Stamina'),
            ('spellshield', 'Spell Shield'),
            ('haste', 'Haste'),
            ('speed', 'Speed'),
            ('armor', 'Armor')
        ]
        self.innate_labels = [
            ('bdy', 'Body'),
            ('str', 'Strength'),
            ('dex', 'Dexterity'),
            ('ref', 'Reflexes'),
            ('int', 'Intelligence')
        ]
        self.resist_labels = [
            ('rmagic', 'Magic'),
            ('rphys', 'Physical'),

        ]
        self.write_ratings()
        self.write_innate()
        self.write_resists()

    def input(self, key):
        if key == "open stats":
            self.header.visible = not self.header.visible
            if self.header.visible:
                self.header.collider = "box"
                self.parent.collider = "box"
            else:
                self.header.collider = None
                self.parent.collider = None

    def update(self):
        # If this causes performance problems, just add a timer slower than every frame
        if self.visible:
            for attr in self.entries:
                self.update_label(attr)

    def write_ratings(self):
        Text(text="Ratings", parent=self, origin=(0, 0), world_scale=(18, 18),
             position=(0.5, -0.5 * self.row_width, -1))
        start_row = 1
        end_row = start_row + math.ceil(len(self.rating_labels) / 2)
        # Rows then columns
        locations = [
            [(self.col_width * (j + 0.5) + 0.01,
              -self.row_width * i - 0.5 * self.row_width, -2)
            for i in range(start_row, end_row)] for j in range(2)
        ]
        # Flatten locations, and only take the number needed
        locations = list(itertools.chain(*locations))[:len(self.rating_labels)]
        for i, loc in enumerate(locations):
            label = self.rating_labels[i][1]
            attr = self.rating_labels[i][0]
            cur = getattr(self.player, attr)
            if attr in self.labels_out_of_max:
                cap = getattr(self.player, "max" + attr)
                fmt = (f"{label}:", "{}/{}")
                txt = self.format_string(fmt, cur, cap)
            else:
                fmt = (f"{label}:", "{}")
                txt = self.format_string(fmt, cur)
            self.entries[attr] = Text(text=txt, parent=self, position=loc, origin=(0, 0),
                 world_scale=self.entry_font_size, color=color.white, font='VeraMono.ttf')
            self.entries[attr].fmt = fmt

    def write_innate(self):
        Text(text="Innate", parent=self, origin=(0, 0), world_scale=(18, 18),
             position=(0.5, (-6 - 0.5) * self.row_width, -2))
        start_row = 3 + math.ceil(len(self.rating_labels) / 2)
        end_row = start_row + math.ceil(len(self.innate_labels) / 2)
        locations = [
            [(self.col_width * (j + 0.5) + 0.01,
              -self.row_width * i - 0.5 * self.row_width, -2)
            for i in range(start_row, end_row)] for j in range(2)
        ]
        locations = list(itertools.chain(*locations))[:len(self.innate_labels)]
        for i, loc in enumerate(locations):
            label = self.innate_labels[i][1]
            attr = self.innate_labels[i][0]
            cur = getattr(self.player, attr)
            fmt = (f"{label}:", "{}")
            txt = self.format_string(fmt, cur)
            self.entries[attr] = Text(text=txt, parent=self, position=loc, origin=(0, 0),
                 world_scale=self.entry_font_size, color=color.white, font='VeraMono.ttf')
            self.entries[attr].fmt = fmt

    def write_resists(self):
        Text(text="Resists", parent=self, origin=(0, 0), world_scale=(18, 18),
             position=(0.5, (-11 - 0.5) * self.row_width, -2))
        start_row = 5 + math.ceil(len(self.rating_labels) / 2) \
                      + math.ceil(len(self.innate_labels) / 2)
        end_row = start_row + math.ceil(len(self.resist_labels) / 2)
        # Rows then columns
        locations = [
            [(self.col_width * (j + 0.5) + 0.01,
              -self.row_width * i - 0.5 * self.row_width, -2)
            for i in range(start_row, end_row)] for j in range(2)
        ]
        locations = list(itertools.chain(*locations))[:len(self.resist_labels)]
        for i, loc in enumerate(locations):
            label = self.resist_labels[i][1]
            attr = self.resist_labels[i][0]
            cur = getattr(self.player, attr)
            fmt = (f"{label}:", "{}")
            txt = self.format_string(fmt, cur)
            self.entries[attr] = Text(text=txt, parent=self, position=loc, origin=(0, 0),
                 world_scale=self.entry_font_size, color=color.white, font='VeraMono.ttf')
            self.entries[attr].fmt = fmt

    def format_string(self, fmt, *args):
        first_part = fmt[0]
        second_part = fmt[1].format(*args)
        length = len(first_part) + len(second_part)
        pad = ' ' * (self.entry_width - length)
        return pad.join([first_part, second_part])

    def update_label(self, attr):
        label = self.entries[attr]
        fmt = label.fmt
        cur = getattr(self.player, attr)
        if attr in self.labels_out_of_max:
            cap = getattr(self.player, "max" + attr)
            txt = self.format_string(fmt, cur, cap)
        else:
            txt = self.format_string(fmt, cur)
        label.text = txt

# class RatingsSection(Entity):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self.rating_labels = [
#             ('health', 'Health'),
#             ('mana', 'Mana'),
#             ('stamina', 'Stamina'),
#             ('spellshield', 'Spell Shield'),
#             ('haste', 'Haste'),
#             ('speed', 'Speed'),
#             ('armor', 'Armor')
#         ]

#         self.write_ratings()
    
#     def write_ratings(self):
#         Text(text="Ratings", parent=self, origin=(0, 0), world_scale=(18, 18),
#              position=(0.5, -1/8))
#         # Rows then columns
#         locations = [
#             [(1/4 * (j + 0.5) + 0.01,
#               -1/4 * i - 1/8)
#             for i in range(1, 5 - j)] for j in range(2)
#         ]
#         for i, loc in enumerate(itertools.chain(*locations)):
#             txt = f"{self.rating_labels[i][1]}: " \
#                   f"{getattr(self.parent.player, self.rating_labels[i][0])}"
#             Text(text=txt, parent=self, position=loc, origin=(0, 0),
#                  world_scale=(14, 14), color=color.white, alpha=255)