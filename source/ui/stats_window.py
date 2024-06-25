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

        # grid(self, 14, 2)

        self.rating_labels = [
            ('health', 'Health'),
            ('mana', 'Mana'),
            ('stamina', 'Stamina'),
            ('spellshield', 'Spell Shield'),
            ('haste', 'Haste'),
            ('speed', 'Speed'),
            ('armor', 'Armor')
        ]
        self.stat_labels = [
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
        self.write_stats()
        self.write_resists()

    def input(self, key):
        if key == "open stats":
            self.header.visible = not self.header.visible

    def write_ratings(self):
        Text(text="Ratings", parent=self, origin=(0, 0), world_scale=(18, 18),
             position=(0.5, -0.5 * self.row_width, -1))
        start_row = 1
        end_row = start_row + math.ceil(len(self.rating_labels) / 2)
        print(start_row, end_row)
        # Rows then columns
        locations = [
            [(self.col_width * (j + 0.5) + 0.01,
              -self.row_width * i - 0.5 * self.row_width, -2)
            for i in range(start_row, end_row)] for j in range(2)
        ]
        locations = list(itertools.chain(*locations))[:len(self.rating_labels)]
        for i, loc in enumerate(locations):
            txt = f"{self.rating_labels[i][1]}: " \
                  f"{getattr(self.player, self.rating_labels[i][0])}"
            Text(text=txt, parent=self, position=loc, origin=(0, 0),
                 world_scale=(14, 14), color=color.white)

    def write_stats(self):
        Text(text="Innate Stats", parent=self, origin=(0, 0), world_scale=(18, 18),
             position=(0.5, (-5 - 0.5) * self.row_width, -2))
        start_row = 2 + math.ceil(len(self.rating_labels) / 2)
        end_row = start_row + math.ceil(len(self.stat_labels) / 2)
        print(start_row, end_row)
        locations = [
            [(self.col_width * (j + 0.5) + 0.01,
              -self.row_width * i - 0.5 * self.row_width, -2)
            for i in range(start_row, end_row)] for j in range(2)
        ]
        locations = list(itertools.chain(*locations))[:len(self.stat_labels)]
        for i, loc in enumerate(locations):
            txt = f"{self.stat_labels[i][1]}: " \
                  f"{getattr(self.player, self.stat_labels[i][0])}"
            Text(text=txt, parent=self, position=loc, origin=(0, 0),
                 world_scale=(14, 14), color=color.white)

    def write_resists(self):
        Text(text="Resists", parent=self, origin=(0, 0), world_scale=(18, 18),
             position=(0.5, (-9 - 0.5) * self.row_width, -2))
        start_row = 3 + math.ceil(len(self.rating_labels) / 2) \
                      + math.ceil(len(self.stat_labels) / 2)
        end_row = start_row + math.ceil(len(self.resist_labels) / 2)
        print(start_row, end_row)
        # Rows then columns
        locations = [
            [(self.col_width * (j + 0.5) + 0.01,
              -self.row_width * i - 0.5 * self.row_width, -2)
            for i in range(start_row, end_row)] for j in range(2)
        ]
        locations = list(itertools.chain(*locations))[:len(self.resist_labels)]
        for i, loc in enumerate(locations):
            txt = f"{self.resist_labels[i][1]}: " \
                  f"{getattr(self.player, self.resist_labels[i][0])}"
            Text(text=txt, parent=self, position=loc, origin=(0, 0),
                 world_scale=(14, 14), color=color.white)


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