from ursina import *
from player import *
from npc import *
from combat import *
from world_gen import *

app = Ursina(borderless=False)
GenerateWorld("zones/demo.json")


player = Player("Player", model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -0.5, 0), position=(0, 1, 0))
npc = NPC("NPC", model='cube', color=color.red, collider="box", scale_y=2, origin=(0, -0.5, 0), position=(10, 0, 10))


moblist = [player.mob, npc.mob]
cb = Combat(moblist)

def update():
    cb.main_combat_loop()
    npc.rotate_namelabel(camera.world_position)

app.run()