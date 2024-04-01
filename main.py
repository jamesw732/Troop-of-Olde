from ursina import *
from player import *
from npc import *
from combat import *

# def make_npc_names(npcs):
    # return [Text(npc.name, scale=20, origin=Vec3(0, 0, 0), position=npc.position + Vec3(0, npc.scale_y, 0)) for npc in npcs]
    # return [Text(npc.name, scale=20, parent=npc, origin=Vec3(0, 0, 0), position=Vec3(0, npc.scale_y, 0)) for npc in npcs]

app = Ursina(borderless=False)

Sky(texture="sky_sunset.jpg")
ground = Entity(model="plane", texture="grass", scale=50, collider="box")
roof = Entity(model="cube", color=color.green, collider="box", origin=(0, 0, 0), position=(-10, 4, -10), scale_x=5, scale_z=5)
ramp = Entity(model="plane", color=color.black, scale=15, collider="box", position=(10, 3.24, -10), rotation=(80, 0, 0))
lopsided= Entity(model="cube", color=color.blue, collider="box", scale=5, origin=(0, 0, 0), position=(-10, 0, 10), rotation=(45, 0, 0))
basement = Entity(model="plane", texture="brick", scale_x=200, scale_z=200, collider="box", position = (0, -100, 0))

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