from ursina import *
import numpy


def attempt_melee_hit(src, tgt):
    # Do a bunch of fancy evasion and accuracy calculations to determine if hit goes through
    if numpy.random.random() < 0.2:
        # It's a miss
        miss_melee_hit(src, tgt)
    else:
        # If hit goes through, do some more fancy calculations to generate a min and max hit
        # Damage is uniform from min to max
        min_hit = 5
        max_hit = 15
        dmg = numpy.random.random_integers(min_hit, max_hit)
        # Compute modifiers for an updated damage
        # Then actually perform the hit
        melee_hit(src, tgt, dmg)

def melee_hit(src, tgt, dmg):
    """Apply a successful melee hit
    src: Character
    tgt: Character
    dmg: int"""
    print(f"{src.name} pummels {tgt.name} for {dmg} damage!")
    tgt.health -= dmg

def miss_melee_hit(src, tgt):
    """Handle a missed melee hit"""
    print(f"You attempted to pummel {tgt.name}, but missed!")