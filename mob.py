"""Stores all internal data for characters, such as stats and ratings"""

from ursina import *

class Mob:
    def __init__(self, character, speed=10):
        self.character = character
        self.maxhealth = 100
        self.health = self.maxhealth
        self.speed = speed
        self.combat = False
        self.target = None
        self.max_combat_timer = 1
        self.combat_timer = 0
        self.attackrange = 5

    def die(self):
        """Actions taken when a mob dies. Update this later."""
        print(f"{self.character.name} perishes.")
        self.character.namelabel.disable()
        self.character.namelabel = None
        self.character.disable()
        del self.character
        del self