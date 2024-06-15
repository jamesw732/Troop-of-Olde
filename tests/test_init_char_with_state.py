from ursina import *
import numpy as np

import add_source_to_path
from source.world_gen import *
from source.character import *
from source.player_controller import *
from source.npc_controller import *

app = Ursina()
testzone_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_zones")
zone = os.path.join(testzone_dir, "basic.json")
world = GenerateWorld(zone)
state = CharacterState(position=Vec3(0, 10, 0), model="cube", collider="box", color="orange", name="Player", speed=30.0, scale=(1, 2, 1))
player = Character(state=state)

assert player.color == color.orange
assert player.speed == 30.0
assert player.model.name == "cube"
assert player.collider.name == "box"