"""Represents the non-physical data and functionality of a character"""

import numpy
from ursina import *

class Mob:
    def __init__(self, character, speed=10):
        self.character = character
        self.maxhealth = 100
        self.health = self.maxhealth
        self.speed = speed
        self.in_combat = False
        self.target = None
        self.max_combat_timer = 0.1
        self.combat_timer = 0
        self.attackrange = 10

        self.alive = True

    def melee_hit(self, damage):
        # Eventually incorporate target's defensive stats to modify the damage,
        # but this capture it in essence
        print(f"{self.character.name} pummels {self.target.character.name} for {damage} damage!")
        self.target.health -= damage

    def attempt_melee_hit(self):
        # Do a bunch of fancy evasion and accuracy calculations to determine if hit goes through
        if numpy.random.random() < 0.2:
            print(f"You attempted to pummel {self.target.character.name}, but missed!")
        else:
            # If hit goes through, do some more fancy calculations to generate a min and max hit
            # Damage is uniform from min to max
            min_hit = 5
            max_hit = 15
            damage = numpy.random.random_integers(min_hit, max_hit)
            # Finally, send it to the target for post-processing
            self.melee_hit(damage)

    def progress_combat_timer(self):
        # Add time.dt to combat timer, if flows over max, attempt hit and subtract max
        self.combat_timer += time.dt
        if self.combat_timer > self.max_combat_timer:
            self.combat_timer -= self.max_combat_timer
            if self.character.get_tgt_hittable(self.target.character):
                self.attempt_melee_hit()