from ursina import *

import math

fists_base_dmg = 2

style_to_method = {
    "fists": "pummels",
    "1h slash": "slashes",
    "2h slash": "slashes",
}

default_cb_attrs = {
    "maxhealth": 0,
    "health": 100,
    "statichealth": 100,
    "maxmana": 0,
    "mana": 100,
    "staticmana": 100,
    "maxstamina": 0,
    "stamina": 100,
    "staticstamina": 100,
    "maxspellshield": 0,
    "spellshield": 0,
    "maxarmor": 0,
    "armor": 0,

    "regenhealth": 0,
    "regenmana": 0,
    "regenstamina": 0,

    "bdy": 0,
    "str": 0,
    "dex": 0,
    "ref": 0,
    "int": 0,
    "hardy": 0,

    "haste": 0,
    "speed": 0,
    "casthaste": 0,
    "castdmg": 0,
    "critdmg": 0,
    "critrate": 0,


    "mh_combat_timer": 0,
    "oh_combat_timer": 0,
    "attackrange": 3
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

default_equipment = {
    "armor": None,
    "ring": None,
    "mh": None,
    "oh": None,
}

default_inventory = {f'{i}': None for i in range(24)}

all_skills = [    # Melee styles
    "1h melee",
    "2h melee",
    "fists",
    "maul",
    # Defensive
    "parry",
    "dodge",
    "shields",
    "riposte",
    # Melee "extra"
    "critical hit",
    "flurry",
    "dual wield",
    # Casting styles
    "enchantment",
    "curse",
    "necromancy",
    "transformation",
]


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