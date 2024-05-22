from ursina import *
from world_gen import *
from character import *
from player_controller import *
from npc_controller import *


app = Ursina()
world = GenerateWorld("data/zones/demo.json")


player = Character("Player", model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -0.5, 0), position=(0, 1, 0))
pc = PlayerController(player)


npcs = world.create_npcs("data/zones/demo_npcs.json")
npc_controllers = [NPC_Controller(npc) for npc in npcs]

def update():
    # Continuous processes local to client
    for npc in npc_controllers:
        if npc.character.namelabel:
            npc.rotate_namelabel(player.world_position - camera.world_position)


app.run()