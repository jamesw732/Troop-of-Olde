"""Tests that a character initializes with states and attributes are as expected"""
from ursina import *
import numpy as np

import add_source_to_path
from source.world_gen import GenerateWorld
from source.character import Character
from source.states.physicalstate import PhysicalState
from source.states.cbstate_base import BaseCombatState
from source.states.container import InitContainer

app = Ursina()
testzone_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_zones")
zone = os.path.join(testzone_dir, "basic.json")
world = GenerateWorld(zone)
physical_state = PhysicalState(position=Vec3(0, 10, 0), model="cube",
                               color="orange", scale=(1, 2, 1),
                               cname="Demo Player", type="player")
combat_state = BaseCombatState(statichealth=100)
inventory_state = InitContainer({"0": 1})
equipment_state = InitContainer({"mh": 2})
player = Character(pstate=physical_state, base_state=combat_state,
                   inventory=inventory_state, equipment=equipment_state)

assert player.color == color.orange
assert player.model.name == "cube"
assert player.collider.name == "box"
assert player.health == 100
assert player.inventory["0"]["name"] == "Bronze Shortsword"
assert player.equipment["mh"]["name"] == "Iron Longsword"
print("Test passed")