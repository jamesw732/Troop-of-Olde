from ursina import *
from player import *
from npc import *
from combat import *
from world_gen import *

app = Ursina(borderless=False)
world = GenerateWorld("zones/demo.json")


player = Player("Player", model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -0.5, 0), position=(0, 1, 0))

npcs = world.create_npcs("zones/demo_npcs.json")
moblist = [player.mob] + [npc.mob for npc in npcs]
cb = Combat(moblist)

def update():
    cb.main_combat_loop()
    for npc in npcs:
        npc.rotate_namelabel(player.world_position - camera.world_position)

app.run()