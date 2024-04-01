"""Controls all NPC collision and movement"""

from ursina import *
from mob import Mob

class NPC(Entity):
    def __init__(self, name, *args, mob=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        if mob:
            self.mob = mob
        else:
            self.mob = Mob(self)