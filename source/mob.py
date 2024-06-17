"""Represents the non-physical data and functionality of a character. Mostly engine-independent."""

import numpy
from ursina import *


mob_state_attrs = {
    "uuid": int,
    "maxhealth": int,
    "health": int,
    "in_combat": bool,
    "target": int          # A uuid
}


class Mob(Entity):
    def __init__(self, *args, character=None, **kwargs):
        super().__init__(*args, *kwargs)
        self.character = character
        if self.character:
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
            self.progress_combat_timer()
        else:
            self.combat_timer = 0

        if self.health <= 0:
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
        if not self.character:
            return
        in_range = distance(self.character, self.target.character) < self.attackrange
        return in_range and self.character.get_tgt_los(self.target.character)

    def bind_to_character(self, character):
        self.character = character
        self.name = self.character.name

    def die(self):
        """Actions taken when a mob dies. Will involve removing persistent effects,
        then deleting everything about the character and mob."""
        print(f"{self.name} perishes.")
        self.alive = False
        if self.character:
            destroy(self.character.controller)
            destroy(self.character.namelabel)
            destroy(self.character)
        destroy(self)


class MobState:
    def __init__(self, mob=None, **kwargs):
        if mob is not None:
            for attr in mob_state_attrs:
                if hasattr(mob, attr):
                    val = getattr(mob, attr)
                    # Only include attrs intentionally set
                    if val is not None:
                        if attr == "target":
                            val = val.uuid
                        setattr(self, attr, val)
        else:
            for attr in mob_state_attrs:
                if attr in kwargs:
                    setattr(self, attr, kwargs[attr])

    def __str__(self):
        return str({attr: getattr(self, attr)
                for attr in mob_state_attrs if hasattr(self, attr)})


def serialize_mob_state(writer, state):
    for attr in mob_state_attrs:
        if hasattr(state, attr):
            val = getattr(state, attr)
            if val is not None:
                writer.write(attr)
                writer.write(val)

def deserialize_mob_state(reader):
    state = MobState()
    while reader.iter.getRemainingSize() > 0:
        attr = reader.read(str)
        val = reader.read(mob_state_attrs[attr])
        setattr(state, attr, val)
    return state




# class MobState:
#     def __init__(self, uuid, maxhealth, health, in_combat, target, mob=None):
#         if mob:
#             self.uuid = mob.uuid
#             self.maxhealth = mob.maxhealth
#             self.health = mob.health
#             self.in_combat = mob.in_combat
#             self.target = mob.target
#         else:
#             self.uuid = uuid
#             self.maxhealth = maxhealth
#             self.health = health
#             self.in_combat = in_combat
#             self.target = target


# def serialize_mob_state(writer, state):
#     writer.write(state.uuid)
#     writer.write(state.maxhealth)
#     writer.write(state.health)
#     writer.write(state.in_combat)
#     writer.write(state.target) # a UUID


# def deserialize_mob_state(reader):
#     state = MobState()
#     state.uuid = reader.read(int)
#     state.maxhealth = reader.read(int)
#     state.health = reader.read(int)
#     state.in_combat = reader.read(bool)
#     state.target = reader.read(int) # a UUID