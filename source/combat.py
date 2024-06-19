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
    hitstring = get_melee_hit_string(src, tgt, dmg=dmg)
    print(hitstring)
    tgt.health -= dmg

def miss_melee_hit(src, tgt):
    """Handle a missed melee hit"""
    hitstring = get_melee_hit_string(src, tgt, miss=True)
    print(hitstring)

def get_melee_hit_string(src, tgt, dmg=0, miss=False):
    style = "pummel"
    if miss:
        return f"{src.name} attempted to {style} {tgt.name}, but missed!"
    return f"{src.name} {style}s {tgt.name} for {dmg} damage!"