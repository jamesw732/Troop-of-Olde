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

player = Character("Player", speed=20, model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -0.5, 0), position=(0, 1, 0))
player_controller = PlayerController(player)

i = 0
def update():
    global i
    rads = i * np.pi / 180
    position = (np.cos(rads), 0.1, np.sin(rads))
    state = CharacterState(0, "Player", position, player.rotation, scale=player.scale, speed=player.speed)
    player.apply_state(state)
    i += 1
    if i > 500:
        print("Passed")
        exit(0)

app.run()
    