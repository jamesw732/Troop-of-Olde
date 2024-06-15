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

box1 = Character("Player1", speed=20, model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -0.5, 0), position=(0, 1, 0))
box2 = Character("Player2", speed=20, model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -0.5, 0), position=(0, 1, 0))
# player_controller = PlayerController(player)

camera.position += Vec3(0, 5, 0)
camera.look_at(box1)

i = 0
def update():
    global i
    rads = i * np.pi / 180
    position1 = (np.cos(rads), 0.1, np.sin(rads))
    state1 = CharacterState(char=box1)
    state1.position = position1
    box1.apply_state(state1)

    position2 = (np.sin(rads), 0.1, np.cos(rads))
    state2 = CharacterState(uuid=0, name="Player", position=position2, rotation=box2.rotation, scale=box2.scale, speed=box2.speed)
    box2.apply_state(state2)
    if i % 100 == 0:
        print(box1.get_state())
        print(box2.get_state())
    i += 1
    if i > 500:
        print("Passed")
        exit(0)

app.run()
    