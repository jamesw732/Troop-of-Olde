"""Represents the physical player/npc entities in game"""
from mob import *
from ursina import *
import numpy

class Character(Entity):
    def __init__(self, name, *args, mob=None, **kwargs):
        super().__init__(*args, **kwargs)
        if mob:
            self.mob = mob
        else:
            self.mob = Mob(self)
        self.name = name
