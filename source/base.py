from ursina import *

import math

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

    "haste": 0,
    "speed": 0,
    "casthaste": 0,

    "afire": 0,
    "acold": 0,
    "aelec": 0,
    "apois": 0,
    "adis": 0,

    "max_combat_timer": 1,
    "combat_timer": 0,
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
    "ear": None,
    "head": None,
    "neck": None,
    "chest": None,
    "back": None,
    "legs": None,
    "hands": None,
    "feet": None,
    "ring": None,
    "mh": None,
    "oh": None,
    "ammo": None,
}