from ursina import *
from world_gen import *
from character import *
from player_controller import *
from npc_controller import *


app = Ursina()
world = GenerateWorld("zones/demo.json")


player = Character("Player", model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -0.5, 0), position=(0, 1, 0))
pc = PlayerController(player)


npcs = world.create_npcs("zones/demo_npcs.json")
npc_controllers = [NPC_Controller(npc) for npc in npcs]
moblist = [player.mob] + [npc.mob for npc in npcs]


app.run()