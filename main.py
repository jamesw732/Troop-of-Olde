from ursina import *
from player import *
from npc import *
from combat import *
from world_gen import *

# def make_npc_names(npcs):
    # return [Text(npc.name, scale=20, origin=Vec3(0, 0, 0), position=npc.position + Vec3(0, npc.scale_y, 0)) for npc in npcs]
    # return [Text(npc.name, scale=20, parent=npc, origin=Vec3(0, 0, 0), position=Vec3(0, npc.scale_y, 0)) for npc in npcs]

app = Ursina(borderless=False)
GenerateWorld("zones/demo.json")


player = Player("Player", model='cube', color=color.orange, scale_y=2, collider="box", origin=(0, -0.5, 0), position=(0, 1, 0))
npc = NPC("NPC", model='cube', color=color.red, collider="box", scale_y=2, origin=(0, -0.5, 0), position=(10, 0, 10))

# npclabels = make_npc_names([npc])
# t = Text("Hello World!", scale=2, origin=Vec3(0, 0, 0), position=npc.position)


moblist = [player.mob, npc.mob]
cb = Combat(moblist)

def update():
    cb.main_combat_loop()
    # t.world_position = Vec3(0, 0, 20)
    # for label in npclabels:
    #     label.look_at(player)

app.run()