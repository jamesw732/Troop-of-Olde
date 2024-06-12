"""Represents the non-physical data and functionality of a character. Mostly engine-independent."""

import numpy
from ursina import *

class Mob(Entity):
    def __init__(self, character, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.character = character
        self.name = self.character.name
        self.maxhealth = 100
        self.health = self.maxhealth
        self.in_combat = False
        self.target = None
        self.max_combat_timer = 0.1
        self.combat_timer = 0
        self.attackrange = 10

        self.alive = True

    def update(self):
        if self.target and self.target.alive and self.in_combat:
            self.mob.progress_combat_timer()
        else:
            self.mob.combat_timer = 0

        if self.mob and self.mob.health <= 0:
            self.die()

    def melee_hit(self, damage):
        """Apply damage, print hit info, send to host/clients"""
        print(f"{self.name} pummels {self.target.name} for {damage} damage!")
        self.target.health -= damage
        # Send hit to host/clients

    def miss_melee_hit(self):
        """Print miss info, send to host/clients"""
        print(f"You attempted to pummel {self.target.name}, but missed!")

    def attempt_melee_hit(self):
        # Do a bunch of fancy evasion and accuracy calculations to determine if hit goes through
        if numpy.random.random() < 0.2:
            # It's a miss
            self.miss_melee_hit()
        else:
            # If hit goes through, do some more fancy calculations to generate a min and max hit
            # Damage is uniform from min to max
            min_hit = 5
            max_hit = 15
            damage = numpy.random.random_integers(min_hit, max_hit)
            # Compute modifiers for an updated damage
            # Then actually perform the hit
            self.melee_hit(damage)

    def progress_combat_timer(self):
        # Add time.dt to combat timer, if flows over max, attempt hit and subtract max
        self.combat_timer += time.dt
        if self.combat_timer > self.max_combat_timer:
            self.combat_timer -= self.max_combat_timer
            if self.get_target_hittable():
                self.attempt_melee_hit()

    def get_target_hittable(self):
        in_range = distance(self.character, self.target.character) < self.attackrange
        return in_range and self.character.get_tgt_los(self.target.character)

    def die(self):
        """Actions taken when a mob dies. Will involve removing persistent effects,
        then deleting everything about the character and mob."""
        print(f"{self.name} perishes.")
        self.alive = False
        destroy(self.character.namelabel)
        destroy(self.character)