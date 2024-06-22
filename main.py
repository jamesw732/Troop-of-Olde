from ursina import *

from source.character import *
from source.player_controller import *
from source.npc_controller import *
from source.world_gen import *
from source.gamestate import *

app = Ursina(borderless=False)
gs.world = GenerateWorld("demo.json")

pstate = PhysicalState(speed=20, model='cube', color="orange", scale=(1, 2, 1), collider="box", origin=(0, -0.5, 0), position=(0, 1, 0))
new_cbstate = CombatState(maxhealth=100, health=100)

player = Character(name="Player", pstate=pstate)
gs.pc = PlayerController(player)

npcs = gs.world.create_npcs("demo_npcs.json")
for npc in npcs:
    npc.controller = NPC_Controller(npc, player)

gs.chars += npcs
gs.chars.append(player)

app.run()