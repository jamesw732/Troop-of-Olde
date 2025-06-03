from ursina import *

import math

fists_base_dmg = 2
default_num_powers = 10
PHYSICS_UPDATE_RATE = 1 / 20

"""
Plan to add:
hardiness - ability to withstand non-physical damage (ie cold, fire, poison, etc). Alternatively,
have an advanced elemental type system
some stat that speeds up GCD/channeling, maybe
some stat that scales power damage
crit damage/rate
"""
default_cb_attrs = {
    "maxhealth": 0,
    "health": 100,
    "statichealth": 100,
    "maxenergy": 100,
    "energy": 0,
    "staticenergy": 100,
    "maxarmor": 0,
    "armor": 0,

    "regenhealth": 0,
    "regenenergy": 0,

    "str": 0,
    "dex": 0,
    "ref": 0,

    "haste": 0,
    "speed": 0,

    "mh_combat_timer": 0,
    "oh_combat_timer": 0,
    "attackrange": 3,

    "gcd": 0,
    "gcd_timer": 0,
    "next_power": None,
}

default_phys_attrs = {
    "model": "cube",
    "scale": Vec3(1, 2, 1),
    "origin": Vec3(0, -.5, 0),
    "collider": "box",
    "color": color.orange,

    "jumping": False,
    "grounded": False,
    "grav": 0,
    "velocity_components": {},
    "height": 2,
    "max_jump_height": 3,
    "rem_jump_height": 3,
    "max_jump_time": 0.3,
    "rem_jump_time": 0.3,

    "traverse_target": scene,

    "alive": True,
    "in_combat": False,
    "target": None
}

default_equipment = [None] * 4
equipment_slots = ["armor", "ring", "mh", "oh"]
slot_to_ind = {"armor": 0, "ring": 1, "mh": 2, "oh": 3}

default_inventory = [None] * 20

# List containing all the stats displayed by the skills window
all_skills = [    # Melee styles
    "1h melee",
    "2h melee",
    "fists",
    # "maul",
    # # Defensive
    # "parry",
    # "dodge",
    # "shields",
    # "riposte",
    # # Melee "extra"
    # "critical hit",
    # "flurry",
    # "dual wield",
    # # Casting styles
    # "enchantment",
    # "curse",
    # "necromancy",
    # "transformation",
]

# List containing all the stats displayed by the stats window, excluding max stats like maxhealth
all_stats = [
    "health",
    "energy",
    "armor",
    "str",
    "ref",
    "dex",
    "haste",
    "speed"
]


def get_speed_modifier(speed):
    return 1 + speed

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def sqnorm(v):
    """Returns the squared norm of a vector.
    v: Any vector"""
    return sum(v ** 2)

def sqdist(v1, v2):
    """Returns the squared distance between two vectors
    v1: Any vector
    v2: Any vector, same shape as v1"""
    return sum((v1 - v2) ** 2)
