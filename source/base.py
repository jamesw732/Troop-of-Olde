from ursina import *

import math
import os

# File/Directory paths
data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
assets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
models_path = os.path.join(assets_path, "models")


fists_base_dmg = 2
PHYSICS_UPDATE_RATE = 1 / 20

all_skills = [
    "1h melee",
    "2h melee",
    "fists",
]
skill_to_idx = {skill: i for i, skill in enumerate(all_skills)}

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

num_equipment_slots = 4
equipment_slots = ["armor", "ring", "mh", "oh"]
slot_to_ind = {"armor": 0, "ring": 1, "mh": 2, "oh": 3}

num_inventory_slots = 20

default_num_powers = 10
power_key_to_slot = {f"power_{i + 1}": i for i in range(default_num_powers)}

# Default values for network-facing character attrs
# Anything used for character creation that's exposed to the network should go here.
default_char_attrs = {
    "cname": "Character",
    "uuid": -1,
    "model_name": "humanoid.glb",
    "model_color": Vec4(0, 0, 0, 1),
    "scale": Vec3(2, 2, 2),
    "position": Vec3(0, 0, 0),
    "rotation": Vec3(0, 0, 0),
    "maxhealth": 100,
    "health": 100,
    "statichealth": 100,
    "maxenergy": 100,
    "energy": 100,
    "staticenergy": 100,
    "armor": 0,
    "str": 0,
    "dex": 0,
    "ref": 0,
    "haste": 0,
    "speed": 0,
    "skills": [1] * len(all_skills),
}

# Default values for internal attrs used to initialize a character
# Anything that shouldn't or can't be exposed to the network should go here
init_char_attrs = {
    "mh_combat_timer": 0,
    "oh_combat_timer": 0,
    "attackrange": 3,
    "gcd": 0,
    "gcd_timer": 0,
    "next_power": None,
    "jumping": False,
    "grounded": False,
    "grav": 0,
    "velocity_components": {},
    "displacement_components": {},
    "height": 2,
    "max_jump_height": 3,
    "rem_jump_height": 3,
    "max_jump_time": 0.3,
    "rem_jump_time": 0.3,
    "traverse_target": scene,
    "ignore_traverse": [],
    "targeted_by": [],
    "alive": True,
    "in_combat": False,
    "target": None,
    "origin": Vec3(0, -.5, 0),
    "equipment": None,
    "inventory": None,
    "powers": [None] * default_num_powers,
}

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

def dot(a, b):
    return sum([i * j for i, j in zip(a, b)])
