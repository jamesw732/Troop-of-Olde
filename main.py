from ursina import *
from source.world_gen import *
from source.character import *
from source.player_controller import *
from source.npc_controller import *

app = Ursina(borderless=False)
world = GenerateWorld("demo.json")

player = Character("Player", speed=20, model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -0.5, 0), position=(0, 1, 0))
player_controller = PlayerController(player)

npcs = world.create_npcs("demo_npcs.json")
for npc in npcs:
    npc.controller = NPC_Controller(npc, player)

chars = npcs + [player]

def update():
    for char in chars:
        if char.namelabel:
            char.rotate_namelabel(player.position - camera.world_position)

app.run()