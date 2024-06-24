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
            ('agi', 'Agility'),
            ('int', 'Intelligence')
        ]
        self.resist_labels = [
            ('rmagic', 'Magic'),
            ('rfire', 'Fire'),
            ('rcold', 'Cold'),
            ('relec', 'Electric'),
            ('rphys', 'Physical'),
            ('rpois', 'Poison'),
            ('rdis', 'Disease')
        ]
        self.write_ratings()
        self.write_stats()
        self.write_resists()
        # grid(self, self.num_rows, self.num_cols)

    def update(self):
        if self.hovered or self.parent.hovered:
            self.alpha = 1
            self.parent.alpha = 1
        else:
            self.alpha = 150 / 255
            self.parent.alpha = 150 / 255

    def input(self, key):
        if key == "open stats":
            self.header.visible = not self.header.visible

    def write_ratings(self):
        Text(text="Ratings", parent=self, origin=(0, 0), world_scale=(18, 18),
             position=(0.5, -0.5 * self.row_width))
        # Rows then columns
        locations = [
            [(self.col_width * (j + 0.5) + 0.01,
              -self.row_width * i - 0.5 * self.row_width)
            for i in range(1, 5 - j)] for j in range(2)
        ]
        for i, loc in enumerate(itertools.chain(*locations)):
            txt = f"{self.rating_labels[i][1]}: " \
                  f"{getattr(self.player, self.rating_labels[i][0])}"
            Text(text=txt, parent=self, position=loc, origin=(0, 0),
                 world_scale=(14, 14), color=color.white, alpha=255)

    def write_stats(self):
        Text(text="Innate Stats", parent=self, origin=(0, 0), world_scale=(18, 18),
             position=(0.5, (-5 - 0.5) * self.row_width))
        locations = [
            [(self.col_width * (j + 0.5) + 0.01,
              -self.row_width * i - 0.5 * self.row_width)
            for i in range(6, 9)] for j in range(2)
        ]
        for i, loc in enumerate(itertools.chain(*locations)):
            txt = f"{self.stat_labels[i][1]}: " \
                  f"{getattr(self.player, self.stat_labels[i][0])}"
            Text(text=txt, parent=self, position=loc, origin=(0, 0),
                 world_scale=(14, 14), color=color.white, alpha=255)

    def write_resists(self):
        Text(text="Resists", parent=self, origin=(0, 0), world_scale=(18, 18),
             position=(0.5, (-9 - 0.5) * self.row_width))
        # Rows then columns
        locations = [
            [(self.col_width * (j + 0.5) + 0.01,
              -self.row_width * i - 0.5 * self.row_width)
            for i in range(10, 14 - j)] for j in range(2)
        ]
        for i, loc in enumerate(itertools.chain(*locations)):
            txt = f"{self.resist_labels[i][1]}: " \
                  f"{getattr(self.player, self.resist_labels[i][0])}"
            Text(text=txt, parent=self, position=loc, origin=(0, 0),
                 world_scale=(14, 14), color=color.white)
